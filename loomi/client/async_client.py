from typing import Any, Literal, Union, overload

from neo4j import AsyncDriver, AsyncSession

from loomi._logger import _LogContextKey, _logger, _scoped_log_ctx
from loomi.client._internal._base import _BaseClient, _ServerType
from loomi.client._internal.session import LoomiAsyncSession
from loomi.exceptions import ClientError


class LoomiAsyncClient(_BaseClient[AsyncDriver]):
    """Async database client for interacting with Loomi models."""

    async def initialize(self) -> None:
        """
        Checks if the remote server is reachable and fetches additional required metadata.

        Raises:
            ClientError: If the remote server can not be reached or does not return required
            metadata.
        """
        try:
            _logger.info("Verifying connectivity to remote")
            await self._driver.verify_connectivity()

            _logger.info("Getting remote server information")
            server_info = await self._driver.get_server_info()

            self._server_type = (
                _ServerType.MEMGRAPH
                if "memgraph" in server_info.agent.lower()
                else _ServerType.NEO4J
            )

            _logger.debug("Checking server version")
            async with self._driver.session() as session:
                query = (
                    "SHOW VERSION"
                    if self._server_type == _ServerType.MEMGRAPH
                    else (
                        "CALL dbms.components() YIELD name, versions "
                        'WHERE name = "Neo4j Kernel" '
                        "RETURN versions[0] AS version"
                    )
                )

                result = await session.run(query)
                version = await result.value()
                if len(version) == 0:
                    raise ClientError("Server did not respond with a valid version")

                self._extract_version(version[0])
        except Exception as exc:
            raise ClientError("Could not get required metadata from remote") from exc

    @overload
    def session(
        self, to_models: Literal[True] = True, **session_config: Any
    ) -> LoomiAsyncSession: ...

    @overload
    def session(self, to_models: Literal[False], **session_config: Any) -> AsyncSession: ...

    def session(
        self,
        to_models: bool = True,
        **session_config: Any,
    ) -> Union[AsyncSession, LoomiAsyncSession]:
        """
        Start a new session. This behaves the same as the `.session()` from the driver except it
        will transform any entities contained in the result of any queries into their corresponding
        models (if possible).

        Args:
            to_models (bool): Whether to transform results into registered models (if possible).
            Defaults to `True`.
            session_config: Key-word arguments passed to the session directly.
        """
        with _scoped_log_ctx(
            {
                _LogContextKey.DRIVER: self._driver.__class__.__name__,
                _LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            session = self._driver.session(**session_config)

            if to_models:
                return LoomiAsyncSession(session, self)

            return session
