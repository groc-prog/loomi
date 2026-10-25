# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


from typing import cast

import neo4j
import neo4j.graph
import pytest

from loomi._sync.client import Client
from loomi._sync.result import Result
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
def seed_data(sync_driver):
    with sync_driver.session() as session:
        session.run(
            "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c)",
            {
                "a": {"name": "John"},
                "b": {"loves": True},
                "c": {"name": "Jane"},
            },
        )


class TestSyncNativeSession:
    def test_sync_session_returns_neo4j_objects_in_native_mode(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.initialize()

        with client.session(mode="native") as session:
            result = session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            assert isinstance(result, neo4j.Result)

            entities = result.values()
            assert len(entities) == 1

            for entity in entities[0]:
                assert isinstance(entity, (neo4j.graph.Node, neo4j.graph.Relationship))


class TestSyncLoomiSession:
    def test_sync_loomi_session_raises_if_model_not_registered(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.initialize()

        with client.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")

            with pytest.raises(SerializationError, match="No model with labels Adult registered"):
                result.values()

        with client.session() as session:
            result = session.run("MATCH ()-[c:HAS_CHILD]->() RETURN c")

            with pytest.raises(SerializationError, match="No model with type HAS_CHILD registered"):
                result.values()

    def test_sync_loomi_session_supports_getattr_usage(self, sync_driver):
        client = Client(sync_driver)
        client.initialize()

        session = client.session()
        result = session.run("MATCH (a:Adult) RETURN a")

        assert isinstance(result, Result)

        session.close()

    def test_sync_loomi_session_passes_kwargs_to_neo4j_session(self, sync_driver, mocker):
        session_spy = mocker.spy(sync_driver, "session")

        client = Client(sync_driver)
        client.initialize()

        test_fetch_size = 1000

        session_spy.reset_mock()
        session = client.session(fetch_size=test_fetch_size)
        session_spy.assert_called_once_with(fetch_size=test_fetch_size)
        session.close()

    def test_sync_loomi_session_returns_unchanged_result_if_strict_transformation_disabled(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            entities = result.values()
            raw_result = cast(neo4j.graph.Node, entities[0][0])

        with client.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            entities = result.values()

            assert len(entities) == 1
            entity = entities[0][0]

            assert isinstance(entity, neo4j.graph.Node)
            assert entity.labels == set(raw_result.labels)
            assert entity["name"] == raw_result["name"]
            assert entity.id == raw_result.id
            assert entity.element_id == raw_result.element_id

    def test_sync_loomi_session_resolves_primitive_value(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            result = session.run("RETURN 2")
            entities = result.values()

            assert len(entities) == 1
            entity = entities[0][0]

            assert isinstance(entity, int)
            assert entity == 2

    def test_sync_loomi_session_resolves_nodes(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            entities = result.values()
            raw_result = cast(neo4j.graph.Node, entities[0][0])

        with client.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            entities = result.values()

            assert len(entities) == 1
            entity = entities[0][0]

            assert isinstance(entity, Adult)
            assert entity.labels() == set(raw_result.labels)
            assert entity.name == raw_result["name"]
            assert entity.id == raw_result.id
            assert entity.element_id == raw_result.element_id

    def test_sync_loomi_session_resolves_relationships(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[c:HAS_CHILD]->() RETURN c")
            entities = result.values()
            raw_result = cast(neo4j.graph.Relationship, entities[0][0])

        with client.session() as session:
            result = session.run("MATCH ()-[c:HAS_CHILD]->() RETURN c")
            entities = result.values()

            assert len(entities) == 1
            entity = entities[0][0]

            assert isinstance(entity, HasChild)
            assert entity.type() == raw_result.type
            assert entity.loves == raw_result["loves"]
            assert entity.id == raw_result.id
            assert entity.element_id == raw_result.element_id

    def test_sync_loomi_session_resolves_path(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run("MATCH p=(:Adult)-[:HAS_CHILD]->(:Child) RETURN p")
            entities = result.values()
            raw_result = cast(neo4j.graph.Path, entities[0][0])

        with client.session() as session:
            result = session.run("MATCH p=(:Adult)-[:HAS_CHILD]->(:Child) RETURN p")
            entities = result.values()

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
                assert any(node.element_id == path_node.element_id for path_node in entity.nodes)

            for relationship in entity.graph.relationships:
                assert any(
                    relationship.element_id == path_relationship.element_id
                    for path_relationship in entity.relationships
                )
