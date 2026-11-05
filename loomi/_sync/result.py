# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, List, Literal, Optional, cast, overload

import neo4j
import neo4j.graph

from loomi._core.result_mixin import ResultMixin
from loomi._core.types import TResultKey
from loomi._sync.change_tracker import ChangeTracker
from loomi.graph.graph import Graph

if TYPE_CHECKING:
    from loomi._sync.client import Client

    _Base = neo4j.Result
else:
    Client = object
    _Base = object


class Result(ResultMixin, _Base):
    __result: neo4j.Result

    def __init__(
        self, result: neo4j.Result, client: Client, change_tracker: Optional[ChangeTracker]
    ):
        self._client = client
        self._change_tracker = change_tracker
        self.__result = result

    def __getattr__(self, name: str):
        return getattr(self.__result, name)

    def __iter__(self):
        iterator = iter(self.__result)

        for record in iterator:
            yield self._resolve_entities(record)

    def __next__(self):
        record = self.__result.__next__()
        return self._resolve_entities(record)

    def peek(self):
        """
        Method providing the same interface as `neo4j.Result.peek`.

        If a entity is returned, it will be transformed to it's corresponding model if that model
        has been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the change tracker.
        """
        record = self.__result.peek()
        if record is None:
            return record

        return self._resolve_entities(record)

    def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.Result.fetch`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        records = self.__result.fetch(n)
        return self._resolve_entities(records)

    def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.Result.to_eager_result`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        eager_result = self.__result.to_eager_result()
        return self._resolve_entities(eager_result)

    @overload
    def single(self, strict: Literal[False] = False) -> Optional[neo4j.Record]: ...

    @overload
    # pylint: disable-next=signature-differs
    def single(self, strict: Literal[True]) -> neo4j.Record: ...

    def single(self, strict: bool = False) -> Optional[neo4j.Record]:
        """
        Method providing the same interface as `neo4j.Result.single`.

        If a entity is returned, it will be transformed to it's corresponding model if that model
        has been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the change tracker.
        """
        record = self.__result.single(strict)
        if record is None:
            return record

        return self._resolve_entities(record)

    def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.Result.values`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        values = self.__result.values(*keys)
        return self._resolve_entities(values)

    def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.Result.value`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        value = self.__result.value(key, default)
        return cast(List[Any], self._resolve_entities(value))

    def graph(self) -> Graph:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Method providing the same interface as `neo4j.Result.graph`. Returns a special
        `Graph` which contains transformed entities.

        Returns:
            Graph: Graph containing transformed entities.
        """
        original_graph = self.__result.graph()
        graph = self._resolve_graph(original_graph)

        graph._relationship_types = {
            type_: self._client._relationship_type_to_model(type_) or relationship
            for type_, relationship in original_graph._relationship_types.items()
        }
        graph._node_set_view = neo4j.graph.EntitySetView(graph._nodes)
        graph._relationship_set_view = neo4j.graph.EntitySetView(graph._relationships)

        return graph
