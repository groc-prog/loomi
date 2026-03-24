from typing import Dict, LiteralString, Union, cast

import neo4j

from loomi._internal._change_tracker import BaseChangeTracker
from loomi._logger import LogContextKey, logger, scoped_log_ctx


class AsyncChangeTracker(BaseChangeTracker[Union[neo4j.AsyncSession, neo4j.AsyncTransaction]]):
    """Manages state synchronization between local entities and the database state."""

    async def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `AsyncSession`, a `new transaction` will be created (based
        on the current session) which will run all queries and `commit them`. If this is called
        on a `AsyncTransaction`, the flushed queries will be `part of that transaction` and
        will only be committed once `tx.commit()` is called.
        """
        with scoped_log_ctx(
            {
                LogContextKey.DRIVER: self._client.__class__.__name__,
                LogContextKey.SERVER_TYPE: self._client._server_type,
            }
        ):
            self._omit_redundant_relationship_operations()

            if isinstance(self._session_or_tx, neo4j.AsyncSession):
                # If the change tracker is called on a session, we create a new transaction and run
                # every operation in that transaction
                await self.__flush_with_session()
            else:
                # If this is called on a transaction already, we pass the responsibility of calling
                # `.commit()` to the caller
                await self.__flush_with_transactions()

        self.clear()

    async def __flush_with_session(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        logger.debug("Flush called on session, creating new transaction to run pending changes")

        async with await cast(neo4j.AsyncSession, self._session_or_tx).begin_transaction() as tx:
            for query, parameters in self._build_node_add_operations():
                result = await tx.run(cast(LiteralString, query), parameters)

                entity_id_map = cast(Dict[int, Union[str, int]], dict(await result.values()))
                id_map.update(entity_id_map)

            queries = [*self._build_relationship_add_operations(id_map)]

            node_update_queries = self._build_node_update_operations()
            if node_update_queries is not None:
                queries.append(node_update_queries)

            relationship_update_queries = self._build_relationship_update_operations()
            if relationship_update_queries is not None:
                queries.append(relationship_update_queries)

            node_delete_queries = self._build_node_delete_operations()
            if node_delete_queries is not None:
                queries.append(node_delete_queries)

            relationship_delete_queries = self._build_relationship_delete_operations()
            if relationship_delete_queries is not None:
                queries.append(relationship_delete_queries)

            for query_info in queries:
                query, parameters = query_info
                result = await tx.run(cast(LiteralString, query), parameters)
                await result.consume()

    async def __flush_with_transactions(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        logger.debug(
            "Flush called on transaction, run pending changes directly on transaction without "
            "committing changes"
        )
        for query, parameters in self._build_node_add_operations():
            result = await self._session_or_tx.run(cast(LiteralString, query), parameters)

            entity_id_map = cast(Dict[int, Union[str, int]], dict(await result.values()))
            id_map.update(entity_id_map)

        queries = [*self._build_relationship_add_operations(id_map)]

        node_update_queries = self._build_node_update_operations()
        if node_update_queries is not None:
            queries.append(node_update_queries)

        relationship_update_queries = self._build_relationship_update_operations()
        if relationship_update_queries is not None:
            queries.append(relationship_update_queries)

        node_delete_queries = self._build_node_delete_operations()
        if node_delete_queries is not None:
            queries.append(node_delete_queries)

        relationship_delete_queries = self._build_relationship_delete_operations()
        if relationship_delete_queries is not None:
            queries.append(relationship_delete_queries)

        for query_info in queries:
            query, parameters = query_info
            result = await self._session_or_tx.run(cast(LiteralString, query), parameters)
            await result.consume()
