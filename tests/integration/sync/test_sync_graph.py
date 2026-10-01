# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

import pickle
from typing import cast

import neo4j
import pytest

from loomi._sync.client import Client
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class GraphPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"GraphPerson"}}


class GraphKnows(Relationship):
    history: list[int]

    loomi_config = {"type": "GRAPH_KNOWS"}


@pytest.fixture
def sync_graph_client(sync_driver: neo4j.Driver):
    client = Client(sync_driver)
    client.initialize()
    client.register(GraphPerson, GraphKnows)
    return client


def create_graph_fixture(sync_driver: neo4j.Driver) -> None:
    with sync_driver.session() as session:
        session.run(
            """
            CREATE (alice:GraphPerson {name: 'Alice', tags: ['alice']})
            CREATE (bob:GraphPerson {name: 'Bob', tags: ['bob']})
            CREATE (alice)-[:GRAPH_KNOWS {history: [2024]}]->(bob)
            """
        )


def fetch_transformed_graph(sync_graph_client) -> Graph:
    with sync_graph_client.session() as session:
        result = session.run(
            "MATCH (start:GraphPerson)-[relationship:GRAPH_KNOWS]->(end) "
            "RETURN start, relationship, end"
        )
        return result.graph()


class TestSyncGraph:
    def test_new_graph_exposes_empty_node_and_relationship_views(self):
        graph = Graph()

        assert len(graph.nodes) == 0
        assert len(graph.relationships) == 0

    def test_relationship_type_returns_and_caches_dynamic_type_for_unknown_name(self):
        graph = Graph()

        relationship_type = graph.relationship_type("UNREGISTERED")

        assert issubclass(relationship_type, neo4j.graph.Relationship)
        assert graph.relationship_type("UNREGISTERED") is relationship_type

    def test_result_graph_exposes_transformed_node_relationship_and_registered_type(
        self, sync_driver: neo4j.Driver, sync_graph_client
    ):
        create_graph_fixture(sync_driver)

        graph = fetch_transformed_graph(sync_graph_client)

        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert {cast(GraphPerson, node).name for node in graph.nodes} == {"Alice", "Bob"}
        assert all(isinstance(node, GraphPerson) for node in graph.nodes)
        assert all(isinstance(relationship, GraphKnows) for relationship in graph.relationships)
        assert graph.relationship_type("GRAPH_KNOWS") is GraphKnows

    def test_pickled_graph_restores_nodes_relationships_and_relationship_type(
        self, sync_driver: neo4j.Driver, sync_graph_client
    ):
        create_graph_fixture(sync_driver)
        graph = fetch_transformed_graph(sync_graph_client)

        restored = pickle.loads(pickle.dumps(graph))

        assert len(restored.nodes) == 2
        assert len(restored.relationships) == 1
        assert {node.name for node in restored.nodes} == {"Alice", "Bob"}
        restored_relationship_type = restored.relationship_type("GRAPH_KNOWS")
        assert issubclass(restored_relationship_type, neo4j.graph.Relationship)
