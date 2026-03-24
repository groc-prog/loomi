# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, List, Literal, Optional, overload

import neo4j
import neo4j.graph

from loomi._internal._types import TResultKey
from loomi._sync.change_tracker import ChangeTracker
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship

if TYPE_CHECKING:
    from loomi._sync.client import Client

    _Base = neo4j.Result
else:
    Client = object
    _Base = object


class Result(_Base):
    """Wrapper for `neo4j.Result` allowing for additional functionality."""

    __result: neo4j.Result
    __client: Client
    __change_tracker: Optional[ChangeTracker]

    def __init__(
        self, result: neo4j.Result, client: Client, change_tracker: Optional[ChangeTracker]
    ):
        self.__result = result
        self.__client = client
        self.__change_tracker = change_tracker

    def __getattr__(self, name: str):
        return getattr(self.__result, name)

    def __iter__(self):
        original_iterator = iter(self.__result)

        for original_record in original_iterator:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                transformed = self.__client._transform_entity(record)
                transformed_record.append((key, transformed))

                self.__add_to_change_tracker(transformed)

            yield neo4j.Record(transformed_record)

    def __next__(self):
        original_result = self.__result.__next__()
        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self.__client._transform_entity(record)
            transformed_result.append((key, transformed))

            self.__add_to_change_tracker(transformed)

        return neo4j.Record(transformed_result)

    def peek(self):
        """
        Method providing the same interface as `neo4j.Result.peek`.

        If a entity is returned, it will be transformed to it's corresponding model if that model
        has been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the `change tracker`.
        """
        original_result = self.__result.peek()
        if original_result is None:
            return original_result

        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self.__client._transform_entity(record)
            transformed_result.append((key, transformed))

            self.__add_to_change_tracker(transformed)

        return neo4j.Record(transformed_result)

    def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.Result.fetch`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self.__result.fetch(n)

        transformed_result: List[neo4j.Record] = []
        for original_record in original_result:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                self.__client._transform_entity(record)
                transformed = self.__client._transform_entity(record)
                transformed_record.append((key, transformed))

                self.__add_to_change_tracker(transformed)

            transformed_result.append(neo4j.Record(transformed_record))

        return transformed_result

    def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.Result.to_eager_result`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self.__result.to_eager_result()

        transformed_result: List[neo4j.Record] = []
        for original_record in original_result.records:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                self.__client._transform_entity(record)
                transformed = self.__client._transform_entity(record)
                transformed_record.append((key, transformed))

                self.__add_to_change_tracker(transformed)

            transformed_result.append(neo4j.Record(transformed_record))

        return neo4j.EagerResult(transformed_result, original_result.summary, original_result.keys)

    @overload
    def single(self, strict: Literal[False] = False) -> neo4j.Record | None: ...

    @overload
    # pylint: disable-next=signature-differs
    def single(self, strict: Literal[True]) -> neo4j.Record: ...

    def single(self, strict: bool = False) -> Optional[neo4j.Record]:
        """
        Method providing the same interface as `neo4j.Result.single`.

        If a entity is returned, it will be transformed to it's corresponding model if that model
        has been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the `change tracker`.
        """
        original_result = self.__result.single(strict)
        if original_result is None:
            return original_result

        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self.__client._transform_entity(record)
            transformed_result.append((key, transformed))

            self.__add_to_change_tracker(transformed)

        return neo4j.Record(transformed_result)

    def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.Result.values`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self.__result.values(*keys)

        transformed_result: List[List[Any]] = []
        for result_list in original_result:
            transformed_list: List[Any] = []

            for result in result_list:
                transformed = self.__client._transform_entity(result)
                transformed_list.append(transformed)

                self.__add_to_change_tracker(transformed)

            transformed_result.append(transformed_list)

        return transformed_result

    def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.Result.value`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self.__result.value(key, default)

        transformed_result: List[Any] = []
        for result in original_result:
            transformed = self.__client._transform_entity(result)
            transformed_result.append(transformed)

            self.__add_to_change_tracker(transformed)

        return transformed_result

    def graph(self) -> Graph:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Method providing the same interface as `neo4j.Result.graph`. Returns a special
        `Graph` which contains transformed entities.

        Returns:
            Graph: Graph containing transformed entities.
        """
        original_result = self.__result.graph()
        graph = Graph()

        for element_id, node in original_result._nodes.items():
            transformed = self.__client._transform_entity(node)
            graph._nodes[element_id] = transformed

            self.__add_to_change_tracker(transformed)

        for element_id, relationship in original_result._relationships.items():
            transformed = self.__client._transform_entity(relationship)
            graph._relationships[element_id] = transformed

            self.__add_to_change_tracker(transformed)

        graph._relationship_types = {
            type_: self.__client._relationship_type_to_model(type_) or relationship
            for type_, relationship in original_result._relationship_types.items()
        }
        graph._node_set_view = neo4j.graph.EntitySetView(graph._nodes)
        graph._relationship_set_view = neo4j.graph.EntitySetView(graph._relationships)

        return graph

    def __add_to_change_tracker(self, value: Any) -> None:
        if self.__change_tracker is not None and isinstance(value, (Node, Relationship)):
            self.__change_tracker.add(value)
