# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, List, Literal, Optional, overload

from neo4j import AsyncResult, EagerResult, Record, Result
from neo4j.graph import EntitySetView

from loomi.client._internal._change_tracker import AsyncChangeTracker, ChangeTracker
from loomi.models.graph import LoomiGraph
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

if TYPE_CHECKING:
    from loomi.client.async_client import LoomiAsyncClient
    from loomi.client.sync_client import LoomiClient

    _Base = Result
    _AsyncBase = AsyncResult
else:
    LoomiClient = object
    LoomiAsyncClient = object

    _Base = object
    _AsyncBase = object


TResultKey = int | str


class LoomiResult(_Base):
    """Wrapper for `neo4j.Result` allowing for additional functionality."""

    _result: Result
    _client: LoomiClient
    _change_tracker: Optional[ChangeTracker]

    def __init__(
        self, result: Result, client: LoomiClient, change_tracker: Optional[ChangeTracker]
    ):
        self._result = result
        self._client = client
        self._change_tracker = change_tracker

    def __getattr__(self, name: str):
        return getattr(self._result, name)

    def __iter__(self):
        original_iterator = iter(self._result)

        for original_record in original_iterator:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                transformed = self._client._transform_entity(record)
                transformed_record.append((key, transformed))

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            yield Record(transformed_record)

    def __next__(self):
        original_result = self._result.__next__()
        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self._client._transform_entity(record)
            transformed_result.append((key, transformed))

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return Record(transformed_result)

    def peek(self):
        """
        Method providing the same interface as `neo4j.Result.peek`.

        If a entity is returned, it will be transformed to it's corresponding model if that model has
        been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the `change tracker`.
        """
        original_result = self._result.peek()
        if original_result is None:
            return original_result

        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self._client._transform_entity(record)
            transformed_result.append((key, transformed))

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return Record(transformed_result)

    def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.Result.fetch`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self._result.fetch(n)

        transformed_result: List[Record] = []
        for original_record in original_result:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                self._client._transform_entity(record)
                transformed = self._client._transform_entity(record)
                transformed_record.append((key, transformed))

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            transformed_result.append(Record(transformed_record))

        return transformed_result

    def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.Result.to_eager_result`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self._result.to_eager_result()

        transformed_result: List[Record] = []
        for original_record in original_result.records:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                self._client._transform_entity(record)
                transformed = self._client._transform_entity(record)
                transformed_record.append((key, transformed))

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            transformed_result.append(Record(transformed_record))

        return EagerResult(transformed_result, original_result.summary, original_result.keys)

    @overload
    def single(self, strict: Literal[False] = False) -> Record | None: ...

    @overload
    # pylint: disable-next=signature-differs
    def single(self, strict: Literal[True]) -> Record: ...

    def single(self, strict: bool = False) -> Optional[Record]:
        """
        Method providing the same interface as `neo4j.Result.single`.

        If a entity is returned, it will be transformed to it's corresponding model if that model has
        been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the `change tracker`.
        """
        original_result = self._result.single(strict)
        if original_result is None:
            return original_result

        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self._client._transform_entity(record)
            transformed_result.append((key, transformed))

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return Record(transformed_result)

    def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.Result.values`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self._result.values(*keys)

        transformed_result: List[List[Any]] = []
        for result_list in original_result:
            transformed_list: List[Any] = []

            for result in result_list:
                transformed = self._client._transform_entity(result)
                transformed_list.append(transformed)

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            transformed_result.append(transformed_list)

        return transformed_result

    def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.Result.value`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = self._result.value(key, default)

        transformed_result: List[Any] = []
        for result in original_result:
            transformed = self._client._transform_entity(result)
            transformed_result.append(transformed)

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return transformed_result

    def graph(self) -> LoomiGraph:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Method providing the same interface as `neo4j.Result.graph`. Returns a special
        `LoomiGraph` which contains transformed entities.

        Returns:
            LoomiGraph: Graph containing transformed entities.
        """
        original_result = self._result.graph()
        graph = LoomiGraph()

        for element_id, node in original_result._nodes.items():
            transformed = self._client._transform_entity(node)
            graph._nodes[element_id] = transformed

            if self._change_tracker is not None and isinstance(transformed, LoomiNode):
                self._change_tracker.add(transformed)

        for element_id, relationship in original_result._relationships.items():
            transformed = self._client._transform_entity(relationship)
            graph._relationships[element_id] = transformed

            if self._change_tracker is not None and isinstance(transformed, LoomiRelationship):
                self._change_tracker.add(transformed)

        graph._relationship_types = {
            type_: self._client._relationship_type_to_model(type_) or relationship
            for type_, relationship in original_result._relationship_types.items()
        }
        graph._node_set_view = EntitySetView(graph._nodes)
        graph._relationship_set_view = EntitySetView(graph._relationships)

        return graph


class LoomiAsyncResult(_AsyncBase):
    """Wrapper for `neo4j.AsyncResult` allowing for additional functionality."""

    _result: AsyncResult
    _client: LoomiAsyncClient
    _change_tracker: Optional[AsyncChangeTracker]

    def __init__(
        self,
        result: AsyncResult,
        client: LoomiAsyncClient,
        change_tracker: Optional[AsyncChangeTracker],
    ):
        self._result = result
        self._client = client
        self._change_tracker = change_tracker

    def __getattr__(self, name: str):
        return getattr(self._result, name)

    async def __aiter__(self):
        original_iterator = aiter(self._result)

        async for original_record in original_iterator:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                transformed = self._client._transform_entity(record)
                transformed_record.append((key, transformed))

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            yield Record(transformed_record)

    async def __anext__(self):
        original_result = await self._result.__anext__()
        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self._client._transform_entity(record)
            transformed_result.append((key, transformed))

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return Record(transformed_result)

    async def peek(self):
        """
        Method providing the same interface as `neo4j.Result.peek`.

        If a entity is returned, it will be transformed to it's corresponding model if that model has
        been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the `change tracker`.
        """
        original_result = await self._result.peek()
        if original_result is None:
            return original_result

        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self._client._transform_entity(record)
            transformed_result.append((key, transformed))

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return Record(transformed_result)

    async def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.Result.fetch`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = await self._result.fetch(n)

        transformed_result: List[Record] = []
        for original_record in original_result:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                self._client._transform_entity(record)
                transformed = self._client._transform_entity(record)
                transformed_record.append((key, transformed))

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            transformed_result.append(Record(transformed_record))

        return transformed_result

    async def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.Result.to_eager_result`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = await self._result.to_eager_result()

        transformed_result: List[Record] = []
        for original_record in original_result.records:
            transformed_record: List[Any] = []
            for key, record in original_record.items():
                self._client._transform_entity(record)
                transformed = self._client._transform_entity(record)
                transformed_record.append((key, transformed))

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            transformed_result.append(Record(transformed_record))

        return EagerResult(transformed_result, original_result.summary, original_result.keys)

    @overload
    async def single(self, strict: Literal[False] = False) -> Record | None: ...

    @overload
    # pylint: disable-next=signature-differs
    async def single(self, strict: Literal[True]) -> Record: ...

    async def single(self, strict: bool = False) -> Optional[Record]:
        """
        Method providing the same interface as `neo4j.Result.single`.

        If a entity is returned, it will be transformed to it's corresponding model if that model has
        been registered with the client.
        If `tracking` has been set to `true`, the entity will be added to the `change tracker`.
        """
        original_result = await self._result.single(strict)
        if original_result is None:
            return original_result

        transformed_result: List[Any] = []
        for key, record in original_result.items():
            transformed = self._client._transform_entity(record)
            transformed_result.append((key, transformed))

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return Record(transformed_result)

    async def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.Result.values`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = await self._result.values(*keys)

        transformed_result: List[List[Any]] = []
        for result_list in original_result:
            transformed_list: List[Any] = []

            for result in result_list:
                transformed = self._client._transform_entity(result)
                transformed_list.append(transformed)

                if self._change_tracker is not None and isinstance(
                    transformed, (LoomiNode, LoomiRelationship)
                ):
                    self._change_tracker.add(transformed)

            transformed_result.append(transformed_list)

        return transformed_result

    async def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.Result.value`.

        All returned entities will be transformed to their corresponding models if that model has been
        registered with the client.
        If `tracking` has been set to `true`, all entities will be added to the `change tracker`.
        """
        original_result = await self._result.value(key, default)

        transformed_result: List[Any] = []
        for result in original_result:
            transformed = self._client._transform_entity(result)
            transformed_result.append(transformed)

            if self._change_tracker is not None and isinstance(
                transformed, (LoomiNode, LoomiRelationship)
            ):
                self._change_tracker.add(transformed)

        return transformed_result

    async def graph(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
    ) -> LoomiGraph:
        """
        Method providing the same interface as `neo4j.Result.graph`. Returns a special
        `LoomiGraph` which contains transformed entities.

        Returns:
            LoomiGraph: Graph containing transformed entities.
        """
        original_result = await self._result.graph()
        graph = LoomiGraph()

        for element_id, node in original_result._nodes.items():
            transformed = self._client._transform_entity(node)
            graph._nodes[element_id] = transformed

            if self._change_tracker is not None and isinstance(transformed, LoomiNode):
                self._change_tracker.add(transformed)

        for element_id, relationship in original_result._relationships.items():
            transformed = self._client._transform_entity(relationship)
            graph._relationships[element_id] = transformed

            if self._change_tracker is not None and isinstance(transformed, LoomiRelationship):
                self._change_tracker.add(transformed)

        graph._relationship_types = {
            type_: self._client._relationship_type_to_model(type_) or relationship
            for type_, relationship in original_result._relationship_types.items()
        }
        graph._node_set_view = EntitySetView(graph._nodes)
        graph._relationship_set_view = EntitySetView(graph._relationships)

        return graph
