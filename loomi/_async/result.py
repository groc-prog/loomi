# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, List, Literal, Optional, cast, overload

import neo4j
import neo4j.graph

from loomi._async.change_tracker import AsyncChangeTracker
from loomi._core.result_mixin import ResultMixin
from loomi._core.types import TResultKey
from loomi.graph.graph import Graph

if TYPE_CHECKING:
    _Base = neo4j.AsyncResult
    from loomi._async.client import AsyncClient
else:
    AsyncClient = object
    _Base = object


class AsyncResult(ResultMixin, _Base):
    __result: neo4j.AsyncResult

    def __init__(
        self,
        result: neo4j.AsyncResult,
        client: AsyncClient,
        change_tracker: Optional[AsyncChangeTracker],
    ):
        self._client = client
        self._change_tracker = change_tracker
        self.__result = result

    def __getattr__(self, name: str):
        return getattr(self.__result, name)

    async def __aiter__(self):
        iterator = aiter(self.__result)

        async for record in iterator:
            yield self._resolve_entities(record)

    async def __anext__(self):
        record = await self.__result.__anext__()
        return self._resolve_entities(record)

    async def peek(self):
        """
        Method providing the same interface as `neo4j.AsyncResultResult.peek`.

        If a entity is returned, it will be transformed to it's corresponding model if that model
        has been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the change tracker.
        """
        record = await self.__result.peek()
        if record is None:
            return record

        return self._resolve_entities(record)

    async def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.AsyncResultResult.fetch`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        records = await self.__result.fetch(n)
        return self._resolve_entities(records)

    async def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.AsyncResultResult.to_eager_result`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        eager_result = await self.__result.to_eager_result()
        return self._resolve_entities(eager_result)

    @overload
    async def single(self, strict: Literal[False] = False) -> Optional[neo4j.Record]: ...

    @overload
    # pylint: disable-next=signature-differs
    async def single(self, strict: Literal[True]) -> neo4j.Record: ...

    async def single(self, strict: bool = False) -> Optional[neo4j.Record]:
        """
        Method providing the same interface as `neo4j.AsyncResultResult.single`.

        If a entity is returned, it will be transformed to it's corresponding model if that model
        has been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the change tracker.
        """
        record = await self.__result.single(strict)
        if record is None:
            return record

        return self._resolve_entities(record)

    async def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.AsyncResultResult.values`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        values = await self.__result.values(*keys)
        return self._resolve_entities(values)

    async def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.AsyncResultResult.value`.

        All returned entities will be transformed to their corresponding models if that model has
        been registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the change tracker.
        """
        value = await self.__result.value(key, default)
        return cast(List[Any], self._resolve_entities(value))

    async def graph(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
    ) -> Graph:
        """
        Method providing the same interface as `neo4j.AsyncResultResult.graph`. Returns a special
        `Graph` which contains transformed entities.

        Returns:
            Graph: Graph containing transformed entities.
        """
        original_graph = await self.__result.graph()
        graph = self._resolve_graph(original_graph)

        graph._relationship_types = {
            type_: self._client._relationship_type_to_model(type_) or relationship
            for type_, relationship in original_graph._relationship_types.items()
        }
        graph._node_set_view = neo4j.graph.EntitySetView(graph._nodes)
        graph._relationship_set_view = neo4j.graph.EntitySetView(graph._relationships)

        return graph
