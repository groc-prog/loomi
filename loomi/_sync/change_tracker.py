from typing import Dict, LiteralString, Union, cast

import neo4j

from loomi._core.change_tracker_mixin import ChangeTrackerMixin
from loomi.logger import get_logger

logger = get_logger("change_tracker")


class ChangeTracker(ChangeTrackerMixin[Union[neo4j.Session, neo4j.Transaction]]):
    def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `Session`, a **new transaction** will be created (based on
        the current session) which will run all queries and commit them. If this is called
        on a `Transaction`, the flushed queries will be **part of that transaction** and
        will only be committed once `tx.commit()` is called.
        """
        is_session = isinstance(self._session_or_tx, neo4j.Session)
        self._omit_redundant_relationship_operations()

        if is_session:
            # If the change tracker is called on a session, we create a new transaction and run
            # every operation in that transaction
            self.__flush_with_session()
        else:
            # If this is called on a transaction already, we pass the responsibility of calling
            # `.commit()` to the caller
            self.__flush_with_transaction()

        self.clear()

    def __flush_with_session(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        logger.debug("Flush called on session, creating new transaction to run pending changes")

        with cast(neo4j.Session, self._session_or_tx).begin_transaction() as tx:
            for query, parameters in self._build_node_add_operations():
                results = tx.run(cast(LiteralString, query), parameters)
                self._hydrate_created_entities("nodes", id_map, results.values())

            for query, parameters in self._build_relationship_add_operations(id_map):
                results = tx.run(cast(LiteralString, query), parameters)
                self._hydrate_created_entities("relationships", id_map, results.values())

            queries = self._build_update_and_delete_operations()
            for query_info in queries:
                query, parameters = query_info
                results = tx.run(cast(LiteralString, query), parameters)
                results.consume()

    def __flush_with_transaction(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        logger.debug(
            "Flush called on transaction, run pending changes directly on transaction "
            "without committing changes"
        )
        for query, parameters in self._build_node_add_operations():
            results = self._session_or_tx.run(cast(LiteralString, query), parameters)
            self._hydrate_created_entities("nodes", id_map, results.values())

        for query, parameters in self._build_relationship_add_operations(id_map):
            results = self._session_or_tx.run(cast(LiteralString, query), parameters)
            self._hydrate_created_entities("relationships", id_map, results.values())

        queries = self._build_update_and_delete_operations()
        for query_info in queries:
            query, parameters = query_info
            results = self._session_or_tx.run(cast(LiteralString, query), parameters)
            results.consume()
