from typing import Any, Literal, Union, overload

import neo4j

from loomi._async.session import AsyncSession
from loomi._internal.base_client import BaseClient, require_server_metadata
from loomi._logger import LogContextKey, logger, scoped_log_ctx
from loomi.constants import ServerType
from loomi.exceptions import ClientError


class AsyncClient(BaseClient[neo4j.AsyncDriver]):
    """Async database client for interacting with Loomi models."""

    async def initialize(self) -> None:
        """
        Checks if the remote server is reachable and fetches additional required metadata.

        Raises:
            ClientError: If the remote server can not be reached or does not return required
                metadata.
        """
        with scoped_log_ctx({LogContextKey.DRIVER: self._driver.__class__.__name__}):
            try:
                logger.info("Verifying connectivity to remote")
                await self._driver.verify_connectivity()

                logger.info("Getting remote server metadata")
                server_info = await self._driver.get_server_info()

                self._server_type = (
                    ServerType.MEMGRAPH
                    if "memgraph" in server_info.agent.lower()
                    else ServerType.NEO4J
                )

                logger.debug("Checking server version")
                async with self._driver.session() as session:
                    query = (
                        "SHOW VERSION"
                        if self._server_type == ServerType.MEMGRAPH
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
    def session(self, mode: Literal["loomi"] = "loomi", **session_config: Any) -> AsyncSession: ...

    @overload
    def session(
        self, mode: Literal["native"] = "native", **session_config: Any
    ) -> neo4j.AsyncSession: ...

    @require_server_metadata
    def session(
        self,
        mode: Union[Literal["native"], Literal["loomi"]] = "loomi",
        **session_config: Any,
    ) -> Union[neo4j.AsyncSession, AsyncSession]:
        """
        Start a new session. This behaves the same as the `.session()` from the driver except it
        exposes additional functionality if `mode` is set to `loomi`.

        Args:
            mode (Union[Literal["native"], Literal["loomi"]]): Whether to use a native session or a
                Loomi session. Defaults to `loomi`.
            session_config: Key-word arguments passed to the session directly.
        """
        with scoped_log_ctx(
            {
                LogContextKey.DRIVER: self._driver.__class__.__name__,
                LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            session = self._driver.session(**session_config)

            if mode == "loomi":
                return AsyncSession(session, self)

            return session
