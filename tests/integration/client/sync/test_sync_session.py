# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, line-too-long, unused-argument

import neo4j
import neo4j.graph

from loomi.client._internal.result import Result
from loomi.client._internal.session import Session
from loomi.client.sync_client import Client
from loomi.models.node import Node
from loomi.models.relationship import Relationship
from tests.integration.fixtures.db import DriverSpec, driver_spec, sync_driver


class TestNativeSession:
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
