# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from typing import cast

import pytest

from loomi._async.client import AsyncClient
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.path import Path
from loomi.graph.relationship import Relationship


class PathPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"PathPerson"}}


class PathKnows(Relationship):
    history: list[int]

    loomi_config = {"type": "PATH_KNOWS"}


@pytest.fixture
async def async_path_client(async_driver):
    client = AsyncClient(async_driver)
    await client.initialize()
    client.register(PathPerson, PathKnows)
    return client


async def create_path_fixture(async_driver) -> None:
    async with async_driver.session() as session:
        await session.run(
            """
            CREATE (alice:PathPerson {name: 'Alice', tags: ['alice']})
            CREATE (bob:PathPerson {name: 'Bob', tags: ['bob']})
            CREATE (alice)-[:PATH_KNOWS {history: [2024]}]->(bob)
            """
        )


async def fetch_path(async_path_client) -> Path:
    async with async_path_client.session() as session:
        result = await session.run(
            "MATCH route=(start:PathPerson)-[:PATH_KNOWS]->(end:PathPerson) RETURN route"
        )
        record = await result.single()
        assert record is not None
        return record["route"]


class TestAsyncPath:
    async def test_nodes_property_returns_transformed_path_nodes(
        self, async_driver, async_path_client
    ):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert [cast(PathPerson, node).name for node in path.nodes] == ["Alice", "Bob"]
        assert all(isinstance(node, PathPerson) for node in path.nodes)

    async def test_start_node_returns_first_path_node(self, async_driver, async_path_client):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert isinstance(path.start_node, PathPerson)
        assert path.start_node.name == "Alice"

    async def test_end_node_returns_last_path_node(self, async_driver, async_path_client):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert isinstance(path.end_node, PathPerson)
        assert path.end_node.name == "Bob"

    async def test_relationships_property_returns_transformed_relationships(
        self, async_driver, async_path_client
    ):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert len(path.relationships) == 1
        assert isinstance(path.relationships[0], PathKnows)
        assert path.relationships[0].history == [2024]

    async def test_len_returns_number_of_relationships(self, async_driver, async_path_client):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert len(path) == 1

    async def test_iteration_yields_path_relationships(self, async_driver, async_path_client):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert list(path) == list(path.relationships)
        assert all(isinstance(relationship, PathKnows) for relationship in path)

    async def test_repr_includes_endpoints_and_path_size(self, async_driver, async_path_client):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)
        representation = repr(path)

        assert "Path start=" in representation
        assert "end=" in representation
        assert "size=1" in representation

    async def test_equal_paths_compare_equal(self, async_driver, async_path_client):
        await create_path_fixture(async_driver)

        first_path = await fetch_path(async_path_client)
        second_path = await fetch_path(async_path_client)

        assert first_path == second_path

    async def test_comparison_with_unrelated_object_returns_not_implemented(
        self, async_driver, async_path_client
    ):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)

        assert path.__eq__(object()) is NotImplemented

    async def test_hash_returns_integer_for_native_driver_entities(self, async_driver):
        await create_path_fixture(async_driver)
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()

        path = await fetch_path(client)

        assert isinstance(hash(path), int)

    async def test_graph_property_returns_graph_with_transformed_entities(
        self, async_driver, async_path_client
    ):
        await create_path_fixture(async_driver)

        path = await fetch_path(async_path_client)
        graph = path.graph

        assert isinstance(graph, Graph)
        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert all(isinstance(node, PathPerson) for node in graph.nodes)
        assert all(isinstance(relationship, PathKnows) for relationship in graph.relationships)
        assert graph.relationship_type("PATH_KNOWS") is PathKnows

    async def test_zero_length_path_has_same_start_and_end_node(
        self, async_driver, async_path_client
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:PathPerson {name: 'Alice', tags: ['alice']})")
            result = await session.run(
                "MATCH route=(person:PathPerson)-[*0..0]->(person) RETURN route"
            )
            record = await result.single()

        assert record is not None
        path = record["route"]
        assert len(path) == 0
        assert path.start_node is path.end_node
        assert path.relationships == ()
        assert list(path) == []
