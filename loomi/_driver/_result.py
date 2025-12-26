# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, List, Literal, Optional, overload

from neo4j import AsyncResult, EagerResult, Record, Result
from neo4j.graph import EntitySetView

from loomi._driver._graph import LoomiGraph

if TYPE_CHECKING:
    from loomi.client.async_client import LoomiAsyncClient
    from loomi.client.sync_client import LoomiClient
else:
    LoomiClient = object
    LoomiAsyncClient = object


TResultKey = int | str


class LoomiResult(Result):
    """
    Wrapper for `neo4j.Result` objects containing nodes and relationships transformed into the
    corresponding Loomi models.
    """

    __result: Result
    __client: LoomiClient

    def __init__(self, result: Result, client: LoomiClient):
        self.__result = result
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__result, name)

    def __iter__(self):
        original_iterator = iter(self.__result)

        for record in original_iterator:
            transformed_record = [
                (key, self.__client._transform_entity(record))
                for key, record in record.items()
            ]
            yield Record(transformed_record)

    def __next__(self):
        return next(iter(self))

    def peek(self):
        """
        Method providing the same interface as `neo4j.Result.peek`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = self.__result.peek()
        if original_result is None:
            return original_result

        transformed_result = [
            (key, self.__client._transform_entity(record))
            for key, record in original_result.items()
        ]

        return Record(transformed_result)

    def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.Result.fetch`. If entities are returned,
        they will be transformed to their corresponding models.
        """
        original_result = self.__result.fetch(n)

        transformed_result: List[Record] = []
        for result in original_result:
            transformed_record = [
                (key, self.__client._transform_entity(record))
                for key, record in result.items()
            ]
            transformed_result.append(Record(transformed_record))

        return transformed_result

    def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.Result.to_eager_result`. If entities are
        returned, they will be transformed to their corresponding models.
        """
        original_result = self.__result.to_eager_result()

        transformed_result: List[Record] = []
        for original_record in original_result.records:
            transformed_record = [
                (key, self.__client._transform_entity(record))
                for key, record in original_record.items()
            ]
            transformed_result.append(Record(transformed_record))

        return EagerResult(
            transformed_result, original_result.summary, original_result.keys
        )

    @overload
    def single(self, strict: Literal[False] = False) -> Record | None: ...

    @overload
    # pylint: disable-next=signature-differs
    def single(self, strict: Literal[True]) -> Record: ...

    def single(self, strict: bool = False) -> Optional[Record]:
        """
        Method providing the same interface as `neo4j.Result.single`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = self.__result.single(strict)
        if original_result is None:
            return original_result

        transformed_result = [
            (key, self.__client._transform_entity(record))
            for key, record in original_result.items()
        ]

        return Record(transformed_result)

    def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.Result.values`. Entities returned in
        the values list will be transformed to their corresponding models.
        """
        original_result = self.__result.values(*keys)

        transformed_result: List[List[Any]] = []
        for result_list in original_result:
            transformed_list: List[Any] = []

            for result in result_list:
                transformed_list.append(self.__client._transform_entity(result))

            transformed_result.append(transformed_list)

        return transformed_result

    def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.Result.value`. Entities returned in
        the values list will be transformed to their corresponding models.
        """
        original_result = self.__result.value(key, default)

        transformed_result: List[Any] = []
        for result in original_result:
            transformed_result.append(self.__client._transform_entity(result))

        return transformed_result

    def graph(self) -> LoomiGraph:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Method providing the same interface as `neo4j.Result.graph`. Returns a special
        `LoomiGraph` which contains transformed entities.

        Returns:
            LoomiGraph: Graph containing transformed entities.
        """
        original_result = self.__result.graph()
        graph = LoomiGraph()

        graph._nodes = {
            element_id: self.__client._transform_entity(node)
            for element_id, node in original_result._nodes.items()
        }
        graph._relationships = {
            element_id: self.__client._transform_entity(relationship)
            for element_id, relationship in original_result._relationships.items()
        }
        graph._relationship_types = {
            type_: self.__client._type_to_model(type_) or relationship
            for type_, relationship in original_result._relationship_types.items()
        }
        graph._node_set_view = EntitySetView(graph._nodes)
        graph._relationship_set_view = EntitySetView(graph._relationships)

        return graph


class LoomiAsyncResult(AsyncResult):
    """
    Wrapper for `neo4j.AsyncResult` objects containing nodes and relationships transformed into the
    corresponding Loomi models.
    """

    __result: AsyncResult
    __client: LoomiAsyncClient

    def __init__(self, result: AsyncResult, client: LoomiAsyncClient):
        self.__result = result
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__result, name)

    async def __aiter__(self):
        original_iterator = aiter(self.__result)

        async for record in original_iterator:
            transformed_record = [
                (key, self.__client._transform_entity(record))
                for key, record in record.items()
            ]
            yield Record(transformed_record)

    async def __anext__(self):
        return await anext(aiter(self))

    async def peek(self):
        """
        Method providing the same interface as `neo4j.Result.peek`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = await self.__result.peek()
        if original_result is None:
            return original_result

        transformed_result = [
            (key, self.__client._transform_entity(record))
            for key, record in original_result.items()
        ]

        return Record(transformed_result)

    async def fetch(self, n: int):
        """
        Method providing the same interface as `neo4j.Result.fetch`. If entities are returned,
        they will be transformed to their corresponding models.
        """
        original_result = await self.__result.fetch(n)

        transformed_result: List[Record] = []
        for result in original_result:
            transformed_record = [
                (key, self.__client._transform_entity(record))
                for key, record in result.items()
            ]
            transformed_result.append(Record(transformed_record))

        return transformed_result

    async def to_eager_result(self):
        """
        Method providing the same interface as `neo4j.Result.to_eager_result`. If entities are
        returned, they will be transformed to their corresponding models.
        """
        original_result = await self.__result.to_eager_result()

        transformed_result: List[Record] = []
        for original_record in original_result.records:
            transformed_record = [
                (key, self.__client._transform_entity(record))
                for key, record in original_record.items()
            ]
            transformed_result.append(Record(transformed_record))

        return EagerResult(
            transformed_result, original_result.summary, original_result.keys
        )

    @overload
    async def single(self, strict: Literal[False] = False) -> Record | None: ...

    @overload
    # pylint: disable-next=signature-differs
    async def single(self, strict: Literal[True]) -> Record: ...

    async def single(self, strict: bool = False) -> Optional[Record]:
        """
        Method providing the same interface as `neo4j.Result.single`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = await self.__result.single(strict)
        if original_result is None:
            return original_result

        transformed_result = [
            (key, self.__client._transform_entity(record))
            for key, record in original_result.items()
        ]

        return Record(transformed_result)

    async def values(self, *keys: TResultKey):
        """
        Method providing the same interface as `neo4j.Result.values`. Entities returned in
        the values list will be transformed to their corresponding models.
        """
        original_result = await self.__result.values(*keys)

        transformed_result: List[List[Any]] = []
        for result_list in original_result:
            transformed_list: List[Any] = []

            for result in result_list:
                transformed_list.append(self.__client._transform_entity(result))

            transformed_result.append(transformed_list)

        return transformed_result

    async def value(self, key=0, default=None):
        """
        Method providing the same interface as `neo4j.Result.value`. Entities returned in
        the values list will be transformed to their corresponding models.
        """
        original_result = await self.__result.value(key, default)

        transformed_result: List[Any] = []
        for result in original_result:
            transformed_result.append(self.__client._transform_entity(result))

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
        original_result = await self.__result.graph()
        graph = LoomiGraph()

        graph._nodes = {
            element_id: self.__client._transform_entity(node)
            for element_id, node in original_result._nodes.items()
        }
        graph._relationships = {
            element_id: self.__client._transform_entity(relationship)
            for element_id, relationship in original_result._relationships.items()
        }
        graph._relationship_types = {
            type_: self.__client._type_to_model(type_) or relationship
            for type_, relationship in original_result._relationship_types.items()
        }
        graph._node_set_view = EntitySetView(graph._nodes)
        graph._relationship_set_view = EntitySetView(graph._relationships)

        return graph
