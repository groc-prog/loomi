# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from typing import cast

import neo4j
import pytest

from loomi._sync.client import Client
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
def sync_path_client(sync_driver: neo4j.Driver):
    client = Client(sync_driver)
    client.initialize()
    client.register(PathPerson, PathKnows)
    return client


def create_path_fixture(sync_driver: neo4j.Driver) -> None:
    with sync_driver.session() as session:
        session.run(
            """
            CREATE (alice:PathPerson {name: 'Alice', tags: ['alice']})
            CREATE (bob:PathPerson {name: 'Bob', tags: ['bob']})
            CREATE (alice)-[:PATH_KNOWS {history: [2024]}]->(bob)
            """
        )


def fetch_path(sync_path_client) -> Path:
    with sync_path_client.session() as session:
        result = session.run(
            "MATCH route=(start:PathPerson)-[:PATH_KNOWS]->(end:PathPerson) RETURN route"
        )
        record = result.single()
        assert record is not None
        return record["route"]


class TestSyncPath:
    def test_nodes_property_returns_transformed_path_nodes(
        self, sync_driver: neo4j.Driver, sync_path_client
    ):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert [cast(PathPerson, node).name for node in path.nodes] == ["Alice", "Bob"]
        assert all(isinstance(node, PathPerson) for node in path.nodes)

    def test_start_node_returns_first_path_node(self, sync_driver: neo4j.Driver, sync_path_client):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert isinstance(path.start_node, PathPerson)
        assert path.start_node.name == "Alice"

    def test_end_node_returns_last_path_node(self, sync_driver: neo4j.Driver, sync_path_client):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert isinstance(path.end_node, PathPerson)
        assert path.end_node.name == "Bob"

    def test_relationships_property_returns_transformed_relationships(
        self, sync_driver: neo4j.Driver, sync_path_client
    ):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert len(path.relationships) == 1
        assert isinstance(path.relationships[0], PathKnows)
        assert path.relationships[0].history == [2024]

    def test_len_returns_number_of_relationships(self, sync_driver: neo4j.Driver, sync_path_client):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert len(path) == 1

    def test_iteration_yields_path_relationships(self, sync_driver: neo4j.Driver, sync_path_client):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert list(path) == list(path.relationships)
        assert all(isinstance(relationship, PathKnows) for relationship in path)

    def test_repr_includes_endpoints_and_path_size(
        self, sync_driver: neo4j.Driver, sync_path_client
    ):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)
        representation = repr(path)

        assert "Path start=" in representation
        assert "end=" in representation
        assert "size=1" in representation

    def test_equal_paths_compare_equal(self, sync_driver, sync_path_client):
        create_path_fixture(sync_driver)

        first_path = fetch_path(sync_path_client)
        second_path = fetch_path(sync_path_client)

        assert first_path == second_path

    def test_comparison_with_unrelated_object_returns_not_implemented(
        self, sync_driver, sync_path_client
    ):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)

        assert path.__eq__(object()) is NotImplemented

    def test_hash_returns_integer_for_native_driver_entities(self, sync_driver):
        create_path_fixture(sync_driver)
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()

        path = fetch_path(client)

        assert isinstance(hash(path), int)

    def test_graph_property_returns_graph_with_transformed_entities(
        self, sync_driver: neo4j.Driver, sync_path_client
    ):
        create_path_fixture(sync_driver)

        path = fetch_path(sync_path_client)
        graph = path.graph

        assert isinstance(graph, Graph)
        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert all(isinstance(node, PathPerson) for node in graph.nodes)
        assert all(isinstance(relationship, PathKnows) for relationship in graph.relationships)
        assert graph.relationship_type("PATH_KNOWS") is PathKnows

    def test_zero_length_path_has_same_start_and_end_node(
        self, sync_driver: neo4j.Driver, sync_path_client
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:PathPerson {name: 'Alice', tags: ['alice']})")
            result = session.run("MATCH route=(person:PathPerson)-[*0..0]->(person) RETURN route")
            record = result.single()

        assert record is not None
        path = record["route"]
        assert len(path) == 0
        assert path.start_node is path.end_node
        assert path.relationships == ()
        assert list(path) == []
