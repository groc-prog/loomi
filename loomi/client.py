from enum import Enum
from typing import Optional, Tuple, Union, cast

from neo4j import AsyncDriver, Driver

from loomi._logger import _LogContextKey, _scoped_log_ctx, logger
from loomi._utils._awaitable import _AwaitableResult
from loomi.models.base import LoomiBaseConfiguration


class _ServerType(Enum):
    NEO4J = 0
    MEMGRAPH = 1


class Client:
    """Database client for interacting with Loomi models."""

    __driver: Union[Driver, AsyncDriver]
    __config: LoomiBaseConfiguration
    __server_type: Optional[_ServerType]
    __server_version: Optional[Tuple[int, ...]]

    def __init__(
        self,
        driver: Union[Driver, AsyncDriver],
        config: Optional[LoomiBaseConfiguration] = None,
    ) -> None:
        self.__driver = driver
        self.__config = config or LoomiBaseConfiguration()
        self.__server_type = None
        self.__server_version = None

    def initialize(self) -> _AwaitableResult[None]:
        """
        Checks if the remote server is reachable and supported. Can be called asynchronously or
        synchronously by chaining `.sync()`.

        Raises:
            RuntimeError: If the remote server does not return a valid version number.
            Exception: If the remote server can not be reached or server metadata can not be
            fetched.
        """
        is_async = isinstance(self.__driver, AsyncDriver)
        with _scoped_log_ctx(
            {_LogContextKey.EXECUTION_MODE: "async" if is_async else "sync"}
        ):
            if is_async:
                return _AwaitableResult(self.__initialize_async())
            return _AwaitableResult(self.__initialize_sync())

    async def __initialize_async(self) -> None:
        try:
            driver = cast(AsyncDriver, self.__driver)
            logger.info("Verifying connectivity to remote")
            await driver.verify_connectivity()

            logger.info("Getting remote server information")
            server_info = await driver.get_server_info()

            self.__server_type = (
                _ServerType.MEMGRAPH
                if "memgraph" in server_info.agent.lower()
                else _ServerType.NEO4J
            )

            logger.debug("Checking server version")
            async with driver.session() as session:
                query = (
                    "SHOW VERSION"
                    if self.__server_type == _ServerType.MEMGRAPH
                    else (
                        "CALL dbms.components() YIELD name, versions"
                        'WHERE name = "Neo4j Kernel"'
                        "RETURN versions[0] AS version"
                    )
                )

                result = await session.run(query)
                version = await result.value()
                if len(version) == 0:
                    raise RuntimeError("Server did not respond with a valid version")

                self.__extract_version(version[0])
        except Exception:
            logger.exception(
                (
                    "Could not connect to remote. Make sure the driver is initialized before ",
                    "initializing the client",
                )
            )

    def __initialize_sync(self) -> None:
        try:
            driver = cast(Driver, self.__driver)
            logger.info("Verifying connectivity to remote")
            driver.verify_connectivity()

            logger.info("Getting remote server information")
            server_info = driver.get_server_info()

            self.__server_type = (
                _ServerType.MEMGRAPH
                if "memgraph" in server_info.agent.lower()
                else _ServerType.NEO4J
            )

            logger.debug("Checking server version")
            with driver.session() as session:
                query = (
                    "SHOW VERSION"
                    if self.__server_type == _ServerType.MEMGRAPH
                    else (
                        "CALL dbms.components() YIELD name, versions "
                        'WHERE name = "Neo4j Kernel" '
                        "RETURN versions[0] AS version"
                    )
                )

                result = session.run(query)
                version = result.value()
                if len(version) == 0:
                    raise RuntimeError("Server did not respond with a valid version")

                self.__extract_version(version[0])
        except Exception:
            logger.exception(
                (
                    "Could not connect to remote. Make sure the driver is initialized before ",
                    "initializing the client",
                )
            )

    def __extract_version(self, version: str) -> None:
        self.__server_version = tuple(int(part) for part in version.split("."))
