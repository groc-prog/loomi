from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, overload

import neo4j
import neo4j.graph

from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.logger import get_logger

if TYPE_CHECKING:
    from loomi._async.change_tracker import AsyncChangeTracker
    from loomi._async.client import AsyncClient
    from loomi._sync.change_tracker import ChangeTracker
    from loomi._sync.client import Client
else:
    AsyncChangeTracker = object
    ChangeTracker = object
    AsyncClient = object
    Client = object

logger = get_logger("driver")

DataType = Union[neo4j.Record, List[neo4j.Record], neo4j.EagerResult, List[List[Any]], List[Any]]


class ResultMixin:
    _client: Union[Client, AsyncClient]
    _change_tracker: Optional[Union[AsyncChangeTracker, ChangeTracker]]

    @overload
    def _resolve_entities(self, data: neo4j.Record) -> neo4j.Record: ...

    @overload
    def _resolve_entities(self, data: List[neo4j.Record]) -> List[neo4j.Record]: ...

    @overload
    def _resolve_entities(self, data: neo4j.EagerResult) -> neo4j.EagerResult: ...

    @overload
    def _resolve_entities(self, data: List[List[Any]]) -> List[List[Any]]: ...

    @overload
    def _resolve_entities(self, data: List[Any]) -> List[Any]: ...

    def _resolve_entities(self, data: DataType) -> DataType:
        cache: Dict[str, Any] = {}

        if isinstance(data, neo4j.Record):
            return self.__resolve_record(cache, data)

        if isinstance(data, list):
            transformed: List[Any] = []

            for value in data:
                if isinstance(value, neo4j.Record):
                    transformed.append(self.__resolve_record(cache, value))
                    continue

                if isinstance(value, list):
                    transformed.append([self.__resolve_value(cache, item) for item in value])
                    continue

                transformed.append(self.__resolve_value(cache, value))

            return transformed

        return self.__resolve_eager_result(cache, data)

    def _resolve_graph(self, graph: neo4j.graph.Graph) -> Graph:
        cache: Dict[str, Any] = {}
        transformed_graph = Graph()

        for element_id, node in graph._nodes.items():
            if len(node.labels) == 0:
                logger.debug(
                    "Node %s does not have labels populated. Node will be skipped from graph",
                    node.element_id,
                )
                continue

            transformed_graph._nodes[element_id] = self.__resolve_value(cache, node)

        for element_id, relationship in graph._relationships.items():
            transformed_graph._relationships[element_id] = self.__resolve_value(cache, relationship)

        return transformed_graph

    def __resolve_eager_result(
        self, cache: Dict[str, Any], eager_result: neo4j.EagerResult
    ) -> neo4j.EagerResult:
        transformed_records: List[neo4j.Record] = []

        for record in eager_result.records:
            transformed_record: List[Any] = []

            for key, value in record.items():
                if isinstance(value, (neo4j.graph.Node, neo4j.graph.Relationship)):
                    cached = cache.get(value.element_id)

                    if cached is not None:
                        logger.debug(
                            "Entity %s already cached, skipping serialization", value.element_id
                        )
                        transformed_record.append(cached)
                        continue

                transformed = self._client._transform_entity(value)
                transformed_record.append((key, transformed))

                if (
                    isinstance(transformed, (Node, Relationship))
                    and transformed.element_id is not None
                ):
                    cache.setdefault(transformed.element_id, transformed)
                    self.__add_to_change_tracker(transformed)

            transformed_records.append(neo4j.Record(transformed_record))

        return neo4j.EagerResult(transformed_records, eager_result.summary, eager_result.keys)

    def __resolve_record(self, cache: Dict[str, Any], record: neo4j.Record) -> neo4j.Record:
        transformed_record: List[Any] = []

        for key, value in record.items():
            if isinstance(value, (neo4j.graph.Node, neo4j.graph.Relationship)):
                cached = cache.get(value.element_id)

                if cached is not None:
                    logger.debug(
                        "Entity %s already cached, skipping serialization", value.element_id
                    )
                    transformed_record.append(cached)
                    continue

            transformed = self._client._transform_entity(value)
            transformed_record.append((key, transformed))

            if isinstance(transformed, (Node, Relationship)) and transformed.element_id is not None:
                cache.setdefault(transformed.element_id, transformed)
                self.__add_to_change_tracker(transformed)

        return neo4j.Record(transformed_record)

    def __resolve_value(self, cache: Dict[str, Any], value: Any) -> Any:
        if isinstance(value, (neo4j.graph.Node, neo4j.graph.Relationship)):
            cached = cache.get(value.element_id)

            if cached is not None:
                logger.debug("Entity %s already cached, skipping serialization", value.element_id)
                return cached

        transformed = self._client._transform_entity(value)

        if isinstance(transformed, (Node, Relationship)) and transformed.element_id is not None:
            cache.setdefault(transformed.element_id, transformed)
            self.__add_to_change_tracker(transformed)

        return transformed

    def __add_to_change_tracker(self, value: Any) -> None:
        if self._change_tracker is not None:
            self._change_tracker.add(value)
