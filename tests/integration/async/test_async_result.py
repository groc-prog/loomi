# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi._async.result import AsyncResult
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class ResultPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"AsyncResultPerson"}}


class ResultKnows(Relationship):
    history: list[int]

    loomi_config = {"type": "ASYNC_RESULT_KNOWS"}


@pytest.fixture
async def async_result_client(async_driver: neo4j.AsyncDriver):
    client = AsyncClient(async_driver)
    await client.initialize()
    client.register(ResultPerson, ResultKnows)
    return client


@pytest.fixture
async def async_result_session(async_result_client):
    async with async_result_client.session() as session:
        yield session


async def create_result_people(async_driver: neo4j.AsyncDriver) -> None:
    async with async_driver.session() as session:
        await session.run(
            """
            CREATE (:AsyncResultPerson {name: 'Alice', tags: ['alice']})
            CREATE (:AsyncResultPerson {name: 'Bob', tags: ['bob']})
            """
        )


async def create_result_graph(async_driver: neo4j.AsyncDriver) -> None:
    async with async_driver.session() as session:
        await session.run(
            """
            CREATE (alice:AsyncResultPerson {name: 'Alice', tags: ['alice']})
            CREATE (bob:AsyncResultPerson {name: 'Bob', tags: ['bob']})
            CREATE (alice)-[:ASYNC_RESULT_KNOWS {history: [2024]}]->(bob)
            """
        )


async def get_result_person_tags(async_driver: neo4j.AsyncDriver) -> list[list[str]]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH (person:AsyncResultPerson) "
            + "RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in await result.data()]


async def get_result_relationship_history(async_driver: neo4j.AsyncDriver) -> list[list[int]]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH ()-[relationship:ASYNC_RESULT_KNOWS]->() "
            "RETURN relationship.history AS history"
        )
        return [record["history"] for record in await result.data()]


class TestAsyncResultIteration:
    async def test_async_iteration_transforms_node_records(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) RETURN person ORDER BY person.name"
        )
        records = [record async for record in result]

        assert [record["person"].name for record in records] == ["Alice", "Bob"]
        assert all(isinstance(record["person"], ResultPerson) for record in records)

    async def test_anext_transforms_next_node_record(self, async_driver, async_result_session):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) RETURN person ORDER BY person.name"
        )
        record = await result.__anext__()

        assert isinstance(record["person"], ResultPerson)
        assert record["person"].name == "Alice"

    async def test_async_iteration_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        async for record in result:
            record["person"].tags = ["iterated"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["iterated"]]

    async def test_anext_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        record = await result.__anext__()
        record["person"].tags = ["anext"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["anext"], ["bob"]]


class TestAsyncResultPeek:
    async def test_peek_transforms_record_without_consuming_it(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person"
        )
        peeked = await result.peek()
        next_record = await result.single()

        assert isinstance(peeked["person"], ResultPerson)
        assert isinstance(next_record["person"], ResultPerson)
        assert peeked["person"].name == next_record["person"].name == "Alice"

    async def test_peek_returns_none_for_empty_result(self, async_result_session):
        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'missing' RETURN person"
        )

        assert await result.peek() is None

    async def test_peek_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        record = await result.peek()
        record["person"].tags = ["peeked"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["peeked"]]


class TestAsyncResultFetch:
    async def test_fetch_transforms_each_node_record(self, async_driver, async_result_session):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) RETURN person ORDER BY person.name"
        )
        records = await result.fetch(2)

        assert [record["person"].name for record in records] == ["Alice", "Bob"]
        assert all(isinstance(record["person"], ResultPerson) for record in records)

    async def test_fetch_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        records = await result.fetch(1)
        records[0]["person"].tags = ["fetched"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["fetched"]]

    async def test_fetch_propagates_underlying_driver_error(self):
        underlying = SimpleNamespace(fetch=AsyncMock(side_effect=RuntimeError("fetch failed")))
        result = AsyncResult(underlying, cast(Any, None), None)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError, match="fetch failed"):
            await result.fetch(1)


class TestAsyncResultEager:
    async def test_to_eager_result_transforms_records(self, async_driver, async_result_session):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) RETURN person ORDER BY person.name"
        )
        eager = await result.to_eager_result()

        assert isinstance(eager, neo4j.EagerResult)
        assert [record["person"].name for record in eager.records] == ["Alice", "Bob"]
        assert all(isinstance(record["person"], ResultPerson) for record in eager.records)

    async def test_to_eager_result_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        eager = await result.to_eager_result()
        eager.records[0]["person"].tags = ["eager"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["eager"]]


class TestAsyncResultSingle:
    async def test_single_transforms_returned_relationship_record(
        self, async_driver, async_result_session
    ):
        await create_result_graph(async_driver)

        result = await async_result_session.run(
            "MATCH ()-[relationship:ASYNC_RESULT_KNOWS]->() RETURN relationship"
        )
        record = await result.single()

        assert record is not None
        assert isinstance(record["relationship"], ResultKnows)
        assert record["relationship"].history == [2024]

    async def test_single_returns_none_when_no_record_exists(self, async_result_session):
        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'missing' RETURN person"
        )

        assert await result.single() is None

    async def test_single_strict_propagates_driver_error_for_empty_result(self):
        underlying = SimpleNamespace(
            single=AsyncMock(side_effect=neo4j.exceptions.ResultNotSingleError("no record"))
        )
        result = AsyncResult(underlying, cast(Any, None), None)  # type: ignore[arg-type]

        with pytest.raises(neo4j.exceptions.ResultNotSingleError):
            await result.single(strict=True)

    async def test_single_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        record = await result.single()
        record["person"].tags = ["single"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["single"]]


class TestAsyncResultValues:
    async def test_values_transforms_requested_entity_column(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) RETURN person ORDER BY person.name"
        )
        values = await result.values("person")

        assert [row[0].name for row in values] == ["Alice", "Bob"]
        assert all(isinstance(row[0], ResultPerson) for row in values)

    async def test_values_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        values = await result.values("person")
        values[0][0].tags = ["values"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["values"]]


class TestAsyncResultValue:
    async def test_value_transforms_entity_list(self, async_driver, async_result_session):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) RETURN person ORDER BY person.name"
        )
        values = await result.value()

        assert [person.name for person in values] == ["Alice", "Bob"]
        assert all(isinstance(person, ResultPerson) for person in values)

    async def test_value_preserves_default_for_empty_values(self, async_result_session):
        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'missing' RETURN person"
        )

        assert await result.value(default="empty") == []

    async def test_value_tracking_persists_mutated_node_on_flush(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        values = await result.value()
        values[0].tags = ["value"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["bob"], ["value"]]


class TestAsyncResultGraph:
    async def test_graph_transforms_nodes_relationship_and_type(
        self, async_driver, async_result_session
    ):
        await create_result_graph(async_driver)

        result = await async_result_session.run(
            "MATCH (start:AsyncResultPerson)-[relationship:ASYNC_RESULT_KNOWS]->(end) "
            "RETURN start, relationship, end"
        )
        graph = await result.graph()

        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert all(isinstance(node, ResultPerson) for node in graph.nodes)
        assert all(isinstance(relationship, ResultKnows) for relationship in graph.relationships)
        assert graph.relationship_type("ASYNC_RESULT_KNOWS") is ResultKnows

    async def test_graph_tracking_persists_mutated_nodes_and_relationship(
        self, async_driver, async_result_session
    ):
        await create_result_graph(async_driver)

        result = await async_result_session.run(
            "MATCH (start:AsyncResultPerson)-[relationship:ASYNC_RESULT_KNOWS]->(end) "
            "RETURN start, relationship, end",
            tracking=True,
        )
        graph = await result.graph()
        for node in graph.nodes:
            node.tags = ["graph"]
        for relationship in graph.relationships:
            relationship.history = [2025]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["graph"], ["graph"]]
        assert await get_result_relationship_history(async_driver) == [[2025]]


class TestAsyncResultTracking:
    async def test_disabled_tracking_does_not_persist_mutated_result_entity(
        self, async_driver, async_result_session
    ):
        await create_result_people(async_driver)

        result = await async_result_session.run(
            "MATCH (person:AsyncResultPerson) WHERE person.name = 'Alice' RETURN person"
        )
        record = await result.single()
        record["person"].tags = ["not-tracked"]
        await async_result_session.change_tracker.flush()

        assert await get_result_person_tags(async_driver) == [["alice"], ["bob"]]

    async def test_tracking_ignores_primitive_result_values(self, async_result_session):
        result = await async_result_session.run("RETURN 42 AS answer", tracking=True)

        record = await result.single()
        assert record["answer"] == 42

        await async_result_session.change_tracker.flush()


class TestAsyncResultDelegation:
    async def test_unknown_attributes_are_delegated_to_native_result(self, async_result_session):
        result = await async_result_session.run("RETURN 1 AS answer")

        assert result.keys() == ["answer"]
