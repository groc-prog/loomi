# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, line-too-long, unused-argument

import pickle

import neo4j
import neo4j.graph

from loomi.client.sync_client import Client
from loomi.models.graph import Graph
from loomi.models.node import Node
from loomi.models.path import Path
from loomi.models.relationship import Relationship
from tests.integration.fixtures.db import DriverSpec, driver_spec, sync_driver


class PickledHuman(Node):
    name: str


class PickledOwns(Relationship): ...


class TestEntityTransformation:
    def test_graph_entities_are_transformed(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that entities inside the graph are transformed."""

        class Human(Node):
            name: str

        class Owns(Relationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = Client(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run(
                "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l"
            )
            graph = result.graph()
            assert len(graph.nodes) == 2
            assert len(graph.relationships) == 2

            for node in graph.nodes:
                if isinstance(node, neo4j.graph.Node):
                    assert node.labels == {"Animal"}

                    properties = dict(node)
                    assert "kind" in properties
                    assert properties["kind"] == "dog"
                else:
                    assert isinstance(node, Human)
                    assert node.name == "John"

            for relationship in graph.relationships:
                if isinstance(relationship, neo4j.graph.Relationship):
                    assert relationship.type == "LOVES"
                else:
                    assert isinstance(relationship, Owns)

            rel_type = graph.relationship_type("OWNS")
            assert rel_type == Owns

    def test_graph_can_be_pickled(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the graph can be pickled."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = Client(sync_driver)
        client.register(PickledHuman, PickledOwns)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run(
                "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l"
            )
            graph = result.graph()

            pickled = pickle.dumps(graph)
            assert isinstance(pickled, bytes)

            loaded = pickle.loads(pickled)
            assert isinstance(loaded, Graph)

    def test_entities_from_path_are_transformed(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that any returned paths have their entities transformed to  equivalents."""

        class Human(Node):
            name: str

        class Owns(Relationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (h:Human {name: $name}), (a:Animal {kind: $kind}), (h)-[:OWNS]->(a)-[:FED_BY]->(h)",
                {"name": "John", "kind": "dog"},
            )

        client = Client(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH p=(:Human)-[:OWNS]->(:Animal)-[:FED_BY]->(:Human) RETURN p")
            data = result.value()
            path = data[0]

            assert isinstance(path, Path)
            assert isinstance(path.start_node, Human)
            assert path.start_node.name == "John"
            assert isinstance(path.end_node, Human)
            assert path.end_node.name == "John"

            for node in path.nodes:
                if isinstance(node, neo4j.graph.Node):
                    assert node.labels == {"Animal"}

                    properties = dict(node)
                    assert "kind" in properties
                    assert properties["kind"] == "dog"
                else:
                    assert isinstance(node, Human)
                    assert node.name == "John"

            for relationship in path.relationships:
                if isinstance(relationship, neo4j.graph.Relationship):
                    assert relationship.type == "FED_BY"
                else:
                    assert isinstance(relationship, Owns)

    def test_path_graph_is_transformed(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the graph inside the path is transformed."""

        class Human(Node):
            name: str

        class Owns(Relationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (h:Human {name: $name}), (a:Animal {kind: $kind}), (h)-[:OWNS]->(a)-[:FED_BY]->(h)",
                {"name": "John", "kind": "dog"},
            )

        client = Client(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH p=(:Human)-[:OWNS]->(:Animal)-[:FED_BY]->(:Human) RETURN p")
            data = result.value()
            path = data[0]
            assert isinstance(path, Path)

            graph = path.graph
            assert len(graph.nodes) == 2
            assert len(graph.relationships) == 2

            for node in graph.nodes:
                if isinstance(node, neo4j.graph.Node):
                    assert node.labels == {"Animal"}

                    properties = dict(node)
                    assert "kind" in properties
                    assert properties["kind"] == "dog"
                else:
                    assert isinstance(node, Human)
                    assert node.name == "John"

            for relationship in graph.relationships:
                if isinstance(relationship, neo4j.graph.Relationship):
                    assert relationship.type == "FED_BY"
                else:
                    assert isinstance(relationship, Owns)

            rel_type = graph.relationship_type("OWNS")
            assert rel_type == Owns
