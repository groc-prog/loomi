# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


from typing import cast

import neo4j
import neo4j.graph
import pytest

from loomi._async.client import AsyncClient
from loomi._async.result import AsyncResult
from loomi.exceptions import SerializationError
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.path import Path
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


class TestAsyncNativeSession:
    async def test_async_transaction_returns_neo4j_objects_in_native_mode(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        await client.initialize()

        async with client.session(mode="native") as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
                assert isinstance(result, neo4j.AsyncResult)

                entities = await result.values()
                assert len(entities) == 1

                for entity in entities[0]:
                    assert isinstance(entity, (neo4j.graph.Node, neo4j.graph.Relationship))


class TestAsyncLoomiSession:
    async def test_async_loomi_transaction_raises_if_model_not_registered(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        await client.initialize()

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH (a:Adult) RETURN a")

                with pytest.raises(
                    SerializationError, match="No model with labels Adult registered"
                ):
                    await result.values()

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH ()-[c:HAS_CHILD]->() RETURN c")

                with pytest.raises(
                    SerializationError, match="No model with type HAS_CHILD registered"
                ):
                    await result.values()

    async def test_async_loomi_transaction_supports_getattr_usage(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()

        session = client.session()
        tx = await session.begin_transaction()
        result = await tx.run("MATCH (a:Adult) RETURN a")

        assert isinstance(result, AsyncResult)

        await tx.rollback()
        await session.close()

    async def test_async_loomi_transaction_passes_args_to_neo4j_transaction(
        self, async_driver, mocker
    ):
        begin_transaction_spy = mocker.spy(neo4j.AsyncSession, "begin_transaction")

        client = AsyncClient(async_driver)
        await client.initialize()

        test_timeout = 10
        test_metadata = {"test": "called"}

        async with client.session() as session:
            await session.begin_transaction(test_metadata, test_timeout)

        begin_transaction_spy.assert_called_once_with(mocker.ANY, test_metadata, test_timeout)

    async def test_async_loomi_transaction_returns_unchanged_result_if_strict_transformation_disabled(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            entities = await result.values()
            raw_result = cast(neo4j.graph.Node, entities[0][0])

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH (a:Adult) RETURN a")
                entities = await result.values()

                assert len(entities) == 1
                entity = entities[0][0]

                assert isinstance(entity, neo4j.graph.Node)
                assert entity.labels == set(raw_result.labels)
                assert entity["name"] == raw_result["name"]
                assert entity.id == raw_result.id
                assert entity.element_id == raw_result.element_id

    async def test_async_loomi_transaction_resolves_primitive_value(self, async_driver):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("RETURN 2")
                entities = await result.values()

                assert len(entities) == 1
                entity = entities[0][0]

                assert isinstance(entity, int)
                assert entity == 2

    async def test_async_loomi_transaction_resolves_nodes(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            entities = await result.values()
            raw_result = cast(neo4j.graph.Node, entities[0][0])

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH (a:Adult) RETURN a")
                entities = await result.values()

                assert len(entities) == 1
                entity = entities[0][0]

                assert isinstance(entity, Adult)
                assert entity.labels() == set(raw_result.labels)
                assert entity.name == raw_result["name"]
                assert entity.id == raw_result.id
                assert entity.element_id == raw_result.element_id

    async def test_async_loomi_transaction_resolves_relationships(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[c:HAS_CHILD]->() RETURN c")
            entities = await result.values()
            raw_result = cast(neo4j.graph.Relationship, entities[0][0])

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH ()-[c:HAS_CHILD]->() RETURN c")
                entities = await result.values()

                assert len(entities) == 1
                entity = entities[0][0]

                assert isinstance(entity, HasChild)
                assert entity.type() == raw_result.type
                assert entity.loves == raw_result["loves"]
                assert entity.id == raw_result.id
                assert entity.element_id == raw_result.element_id

    async def test_async_loomi_transaction_resolves_path(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH p=(:Adult)-[:HAS_CHILD]->(:Child) RETURN p")
            entities = await result.values()
            raw_result = cast(neo4j.graph.Path, entities[0][0])

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run("MATCH p=(:Adult)-[:HAS_CHILD]->(:Child) RETURN p")
                entities = await result.values()

                assert len(entities) == 1
                entity = entities[0][0]

                assert isinstance(entity, Path)
                assert entity.start_node.element_id == raw_result.start_node.element_id
                assert entity.end_node.element_id == raw_result.end_node.element_id

                assert len(entity.nodes) == 2
                assert all(isinstance(node, Node) for node in entity.nodes)

                assert len(entity.relationships) == 1
                assert all(
                    isinstance(relationship, Relationship) for relationship in entity.relationships
                )

                assert isinstance(entity.graph, Graph)
                for node in entity.graph.nodes:
                    assert any(
                        node.element_id == path_node.element_id for path_node in entity.nodes
                    )

                for relationship in entity.graph.relationships:
                    assert any(
                        relationship.element_id == path_relationship.element_id
                        for path_relationship in entity.relationships
                    )
