# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import pickle

import neo4j
import neo4j.graph
import pytest

from loomi._sync.client import Client
from loomi._sync.result import Result
from loomi._sync.session import Session
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.path import Path
from loomi.graph.relationship import Relationship
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class PickledHuman(Node):
    name: str


class PickledOwns(Relationship): ...


class TestEntityTransformation:
    @pytest.mark.integration
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

    @pytest.mark.integration
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

    @pytest.mark.integration
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

    @pytest.mark.integration
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


class TestNativeSession:
    @pytest.mark.integration
    def test_session_works_with_context_manager(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the session behaves like the original session without transformation when
        used with a context manager.
        """

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            assert isinstance(session, neo4j.Session)

            result = session.run("MATCH (n:Human) RETURN n")
            assert isinstance(result, neo4j.Result)

            data = result.value()
            assert isinstance(data, list)

            node = data[0]
            assert isinstance(node, neo4j.graph.Node)
            assert node.labels == {"Human"}

            properties = dict(node)
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_session_works_with_manual_management(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the session behaves like the original session without transformation when
        session is managed manually.
        """

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("native")
        assert isinstance(session, neo4j.Session)

        result = session.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, neo4j.Result)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, neo4j.graph.Node)
        assert node.labels == {"Human"}

        properties = dict(node)
        assert "name" in properties
        assert properties["name"] == "John"

        session.close()

    @pytest.mark.integration
    def test_transaction_works_with_context_manager(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when used with a context manager.
        """

        class Human(Node):
            name: str

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            assert isinstance(session, neo4j.Session)

            with session.begin_transaction() as tx:
                assert isinstance(tx, neo4j.Transaction)

                tx.run("CREATE (:Human {name: $name})", {"name": "John"})

                result = tx.run("MATCH (n:Human) RETURN n")
                assert isinstance(result, neo4j.Result)

                data = result.value()
                assert isinstance(data, list)

                node = data[0]
                assert isinstance(node, neo4j.graph.Node)
                assert node.labels == {"Human"}

                properties = dict(node)
                assert "name" in properties
                assert properties["name"] == "John"

    @pytest.mark.integration
    def test_transaction_works_with_manual_management(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when transaction is managed manually.
        """

        class Human(Node):
            name: str

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("native")
        assert isinstance(session, neo4j.Session)

        tx = session.begin_transaction()
        assert isinstance(tx, neo4j.Transaction)

        tx.run("CREATE (:Human {name: $name})", {"name": "John"})

        result = tx.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, neo4j.Result)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, neo4j.graph.Node)
        assert node.labels == {"Human"}

        properties = dict(node)
        assert "name" in properties
        assert properties["name"] == "John"

        tx.commit()
        tx.close()
        session.close()


class TestSession:
    @pytest.mark.integration
    def test_session_works_with_context_manager(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the session behaves like the original session with transformation when
        used with a context manager.
        """

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            assert isinstance(session, Session)

            result = session.run("MATCH (n:Human) RETURN n")
            assert isinstance(result, Result)

            data = result.value()
            assert isinstance(data, list)

            node = data[0]
            assert isinstance(node, Human)
            assert node.name == "John"

    @pytest.mark.integration
    def test_session_works_with_manual_management(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the session behaves like the original session with transformation when
        session is managed manually.
        """

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("loomi")
        assert isinstance(session, Session)

        result = session.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, Result)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Human)
        assert node.name == "John"

        session.close()

    @pytest.mark.integration
    def test_session_partially_resolves_entities(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that only registered models get transformed."""

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
            assert isinstance(session, Session)

            result = session.run(
                "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l, 'value'"
            )
            assert isinstance(result, Result)

            data = result.values()
            assert isinstance(data, list)

            animal = data[0][0]
            assert isinstance(animal, Human)
            assert animal.name == "John"

            animal = data[0][1]
            assert isinstance(animal, neo4j.graph.Node)
            assert animal.labels == {"Animal"}

            animal_properties = dict(animal)
            assert "kind" in animal_properties
            assert animal_properties["kind"] == "dog"

            owns = data[0][2]
            assert isinstance(owns, Owns)

            loves = data[0][3]
            assert isinstance(loves, neo4j.graph.Relationship)
            assert loves.type == "LOVES"

            primitive = data[0][4]
            assert isinstance(primitive, str)
            assert primitive == "value"
