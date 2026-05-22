from typing import (
    Any,
    Awaitable,
    Dict,
    List,
    Literal,
    LiteralString,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import neo4j

from loomi._async.session import AsyncSession
from loomi._internal.base_client import BaseClient, require_server_metadata
from loomi._internal.query_builder.delete import DeleteQueryBuilder, _DeleteQueryState, DeleteResult
from loomi._internal.query_builder.match import MatchQueryBuilder, _MatchQueryState
from loomi._internal.query_builder.update import _UpdateQueryState, UpdateQueryBuilder, UpdateResult
from loomi._logger import LogContextKey, logger, scoped_log_ctx
from loomi.constants import ServerType
from loomi.exceptions import ClientError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query._context import CompilationContext

T = TypeVar("T", bound=Union[Node, Relationship])


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

    @require_server_metadata
    def query(
        self,
        model_type: Type[T],
        transaction: Optional[neo4j.AsyncTransaction] = None,
        **kwparameters: Any,
    ):
        """
        A query builder for fetching entities for a given model type.

        Args:
            transaction (Optional[neo4j.AsyncTransaction]): A transaction to use. Defaults to
            `None`.
            kwparameters: Key-word arguments passed to the session/transaction directly.
        """

        async def execute(query: str, parameters: Dict[str, Any]):
            if transaction is not None:
                query_result = await transaction.run(
                    cast(LiteralString, query), parameters, **kwparameters
                )

                result_keys = query_result.keys()
                results = await query_result.values()
            else:
                async with self.session(**kwparameters) as session:
                    query_result = await session.run(
                        cast(LiteralString, query), parameters, **kwparameters
                    )

                    result_keys = query_result.keys()
                    results = await query_result.values()

            if (
                len(results) == 0
                or len(results[0]) == 0
                or isinstance(results[0][0], (Node, Relationship))
            ):
                return [result[0] for result in results]

            transformed_results = []
            for result in results:
                transformed: Dict[str, Any] = {}
                for index, field_name in enumerate(result_keys):
                    transformed[field_name] = result[index]

                transformed_results.append(transformed)

            return transformed_results

        state = _MatchQueryState(model_type)
        ctx = CompilationContext(cast(ServerType, self._server_type))
        ctx.add_model(model_type)

        return MatchQueryBuilder[T, Awaitable[List[T]]](execute, state, ctx)

    @require_server_metadata
    def delete(
        self,
        model_type: Type[T],
        transaction: Optional[neo4j.AsyncTransaction] = None,
        **kwparameters: Any,
    ):
        """
        A query builder for deleting entities for a given model type.

        Args:
            transaction (Optional[neo4j.AsyncTransaction]): A transaction to use. Defaults to
            `None`.
            kwparameters: Key-word arguments passed to the session/transaction directly.
        """

        async def execute(query: str, parameters: Dict[str, Any]):
            if transaction is not None:
                query_result = await transaction.run(
                    cast(LiteralString, query), parameters, **kwparameters
                )
                results = await query_result.values()
            else:
                async with self.session(**kwparameters) as session:
                    query_result = await session.run(
                        cast(LiteralString, query), parameters, **kwparameters
                    )
                    results = await query_result.values()

            affected_entities = [(cast(str, result[0]), cast(int, result[1])) for result in results]
            return DeleteResult(len(affected_entities), affected_entities)

        state = _DeleteQueryState(model_type)
        ctx = CompilationContext(cast(ServerType, self._server_type))
        ctx.add_model(model_type)

        return DeleteQueryBuilder[Awaitable[DeleteResult]](execute, state, ctx)

    @require_server_metadata
    def update(
        self,
        model_type: Type[T],
        transaction: Optional[neo4j.AsyncTransaction] = None,
        **kwparameters: Any,
    ):
        """
        A query builder for updating entities for a given model type.

        Args:
            transaction (Optional[neo4j.AsyncTransaction]): A transaction to use. Defaults to
            `None`.
            kwparameters: Key-word arguments passed to the session/transaction directly.
        """

        async def execute(query: str, parameters: Dict[str, Any]):
            if transaction is not None:
                query_result = await transaction.run(
                    cast(LiteralString, query), parameters, **kwparameters
                )
                results = await query_result.values()
            else:
                async with self.session(**kwparameters) as session:
                    query_result = await session.run(
                        cast(LiteralString, query), parameters, **kwparameters
                    )
                    results = await query_result.values()

            affected_entities = [(cast(str, result[0]), cast(int, result[1])) for result in results]
            return UpdateResult(len(affected_entities), affected_entities)

        state = _UpdateQueryState(model_type)
        ctx = CompilationContext(cast(ServerType, self._server_type))
        ctx.add_model(model_type)

        return UpdateQueryBuilder[Awaitable[UpdateResult]](execute, state, ctx)
