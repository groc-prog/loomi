# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi.exceptions import SerializationError
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class Adult(Node):
    name: str

    loomi_config = {"labels": {"Adult"}}


class Child(Node):
    name: str

    loomi_config = {"labels": {"Child"}}


class HasChild(Relationship):
    loves: bool

    loomi_config = {"type": "HAS_CHILD"}


@pytest.fixture
async def seed_data(async_driver):
    async with async_driver.session() as session:
        await session.run(
            "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c)",
            {
                "a": {"name": "John"},
                "b": {"loves": True},
                "c": {"name": "Jane"},
            },
        )


class TestAsyncLoomiResult:
    async def test_async_loomi_result_peek_returns_models(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            record = await result.peek()

            assert isinstance(record, neo4j.Record)
            for model in record.values():
                assert isinstance(model, (Node, Relationship))

    async def test_async_loomi_result_peek_returns_none(self, async_driver):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            record = await result.peek()

            assert record is None

    async def test_async_loomi_result_fetch_returns_models(self, async_driver, seed_data, mocker):
        fetch_spy = mocker.spy(neo4j.AsyncResult, "fetch")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            records = await result.fetch(10)

            fetch_spy.assert_called_once_with(mocker.ANY, 10)

            assert isinstance(records, list)
            for record in records:
                assert isinstance(record, neo4j.Record)

                models = record.values()
                assert all(isinstance(model, (Node, Relationship)) for model in models)

    async def test_async_loomi_result_to_eager_result_returns_models(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            eager_result = await result.to_eager_result()

            assert isinstance(eager_result, neo4j.EagerResult)
            assert isinstance(eager_result.keys, list)
            assert all(key in ["a", "b", "c"] for key in eager_result.keys)
            assert isinstance(eager_result.summary, neo4j.ResultSummary)
            assert isinstance(eager_result.records, list)

            for record in eager_result.records:
                assert isinstance(record, neo4j.Record)

                models = record.values()
                assert all(isinstance(model, (Node, Relationship)) for model in models)

    async def test_async_loomi_result_single_returns_models(self, async_driver, seed_data, mocker):
        single_spy = mocker.spy(neo4j.AsyncResult, "single")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            record = await result.single(False)

            single_spy.assert_called_once_with(mocker.ANY, False)
            assert isinstance(record, neo4j.Record)

            models = record.values()
            assert all(isinstance(model, (Node, Relationship)) for model in models)

    async def test_async_loomi_result_values_returns_models(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            results = await result.values()

            assert isinstance(results, list)
            assert len(results) == 1

            for result in results[0]:
                assert isinstance(result, (Node, Relationship))

    async def test_async_loomi_result_values_passes_args_to_original_method(
        self, async_driver, seed_data, mocker
    ):
        values_spy = mocker.spy(neo4j.AsyncResult, "values")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a.name, labels(a)")
            results = await result.values(1, 0)

            values_spy.assert_called_once_with(mocker.ANY, 1, 0)
            assert isinstance(results, list)
            assert len(results) == 1

            result = results[0]
            assert result[0] == ["Adult"]
            assert result[1] == "John"

    async def test_async_loomi_result_value_returns_models(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            results = await result.value()

            assert isinstance(results, list)
            assert len(results) == 1

            assert isinstance(results[0], (Node, Relationship))

    async def test_async_loomi_result_value_passes_args_to_original_method(
        self, async_driver, seed_data, mocker
    ):
        value_spy = mocker.spy(neo4j.AsyncResult, "value")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a.name, labels(a)")
            results = await result.value(1)

            value_spy.assert_any_call(mocker.ANY, 1, None)
            assert isinstance(results, list)
            assert len(results) == 1

            assert results[0] == ["Adult"]

    async def test_async_loomi_result_graph_returns_models(self, async_driver, seed_data, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            graph = await result.graph()

            assert isinstance(graph, Graph)
            for node in graph.nodes:
                assert any(node.element_id == path_node.element_id for path_node in graph.nodes)

            for relationship in graph.relationships:
                assert any(
                    relationship.element_id == path_relationship.element_id
                    for path_relationship in graph.relationships
                )

    async def test_async_loomi_result_iter_returns_models(self, async_driver, seed_data, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")

            async for record in result:
                assert isinstance(record, neo4j.Record)
                assert all(isinstance(model, (Node, Relationship)) for model in record.values())

    async def test_async_loomi_result_next_returns_models(self, async_driver, seed_data, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")

            record = await anext(result)
            assert isinstance(record, neo4j.Record)

            assert all(isinstance(model, (Node, Relationship)) for model in record.values())

    async def test_async_loomi_result_passes_non_overwritten_methods_to_neo4j_result(
        self, async_driver, seed_data, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            records = await result.data()

            assert isinstance(records, list)

            data = records[0]
            assert "a" in data
            assert data["a"] == {"name": "John"}
            assert "b" in data
            assert data["b"] == ({"name": "John"}, "HAS_CHILD", {"name": "Jane"})
            assert "c" in data
            assert data["c"] == {"name": "Jane"}
