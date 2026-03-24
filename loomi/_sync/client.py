from typing import Any, Literal, Union, overload

import neo4j

from loomi._internal._base_client import BaseClient, require_server_metadata
from loomi._logger import LogContextKey, logger, scoped_log_ctx
from loomi._sync.session import Session
from loomi.constants import ServerType
from loomi.exceptions import ClientError


class Client(BaseClient[neo4j.Driver]):
    """Sync database client for interacting with Loomi models."""

    def initialize(self) -> None:
        """
        Checks if the remote server is reachable and fetches additional required metadata.

        Raises:
            ClientError: If the remote server can not be reached or does not return required
                metadata.
        """
        try:
            logger.info("Verifying connectivity to remote")
            self._driver.verify_connectivity()

            logger.info("Getting remote server metadata")
            server_info = self._driver.get_server_info()

            self._server_type = (
                ServerType.MEMGRAPH if "memgraph" in server_info.agent.lower() else ServerType.NEO4J
            )

            logger.debug("Checking server version")
            with self._driver.session() as session:
                query = (
                    "SHOW VERSION"
                    if self._server_type == ServerType.MEMGRAPH
                    else (
                        "CALL dbms.components() YIELD name, versions "
                        'WHERE name = "Neo4j Kernel" '
                        "RETURN versions[0] AS version"
                    )
                )

                result = session.run(query)
                version = result.value()
                if len(version) == 0:
                    raise ClientError("Server did not respond with a valid version")

                self._extract_version(version[0])
        except Exception as exc:
            raise ClientError("Could not get required metadata from remote") from exc

    @overload
    def session(self, mode: Literal["loomi"] = "loomi", **session_config: Any) -> Session: ...

    @overload
    def session(
        self, mode: Literal["native"] = "native", **session_config: Any
    ) -> neo4j.Session: ...

    @require_server_metadata
    def session(
        self,
        mode: Union[Literal["native"], Literal["loomi"]] = "loomi",
        **session_config: Any,
    ) -> Union[neo4j.Session, Session]:
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
                return Session(session, self)

            return session
