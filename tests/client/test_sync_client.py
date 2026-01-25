# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, line-too-long

import pickle

from neo4j import Driver, EagerResult, Result, Session, Transaction
from neo4j.graph import Graph, Node, Relationship

from loomi.client._internal.result import LoomiResult
from loomi.client._internal.session import LoomiSession
from loomi.client._internal.transaction import LoomiTransaction
from loomi.client.sync_client import LoomiClient
from loomi.models.graph import LoomiGraph
from loomi.models.node import LoomiNode
from loomi.models.path import LoomiPath
from loomi.models.relationship import LoomiRelationship
from tests.fixtures.db import sync_driver


class TestNativeSession:
    def test_session_works_with_context_manager(self, sync_driver: Driver):
        """
        Verify that the session behaves like the original session without transformation when
        used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            assert isinstance(session, Session)

            result = session.run("MATCH (n:Human) RETURN n")
            assert isinstance(result, Result)

            data = result.value()
            assert isinstance(data, list)

            node = data[0]
            assert isinstance(node, Node)
            assert node.labels == {"Human"}

            properties = dict(node)
            assert "name" in properties
            assert properties["name"] == "John"

    def test_session_works_with_manual_management(self, sync_driver: Driver):
        """
        Verify that the session behaves like the original session without transformation when
        session is managed manually.
        """

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("native")
        assert isinstance(session, Session)

        result = session.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, Result)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Node)
        assert node.labels == {"Human"}

        properties = dict(node)
        assert "name" in properties
        assert properties["name"] == "John"

        session.close()

    def test_transaction_works_with_context_manager(self, sync_driver: Driver):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            assert isinstance(session, Session)

            with session.begin_transaction() as tx:
                assert isinstance(tx, Transaction)

                tx.run("CREATE (:Human {name: $name})", {"name": "John"})

                result = tx.run("MATCH (n:Human) RETURN n")
                assert isinstance(result, Result)

                data = result.value()
                assert isinstance(data, list)

                node = data[0]
                assert isinstance(node, Node)
                assert node.labels == {"Human"}

                properties = dict(node)
                assert "name" in properties
                assert properties["name"] == "John"

    def test_transaction_works_with_manual_management(self, sync_driver: Driver):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when transaction is managed manually.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("native")
        assert isinstance(session, Session)

        tx = session.begin_transaction()
        assert isinstance(tx, Transaction)

        tx.run("CREATE (:Human {name: $name})", {"name": "John"})

        result = tx.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, Result)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Node)
        assert node.labels == {"Human"}

        properties = dict(node)
        assert "name" in properties
        assert properties["name"] == "John"

        tx.commit()
        tx.close()
        session.close()


class TestLoomiSession:
    def test_session_works_with_context_manager(self, sync_driver: Driver):
        """
        Verify that the session behaves like the original session with transformation when
        used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            assert isinstance(session, LoomiSession)

            result = session.run("MATCH (n:Human) RETURN n")
            assert isinstance(result, LoomiResult)

            data = result.value()
            assert isinstance(data, list)

            node = data[0]
            assert isinstance(node, Human)
            assert node.name == "John"

    def test_session_works_with_manual_management(self, sync_driver: Driver):
        """
        Verify that the session behaves like the original session with transformation when
        session is managed manually.
        """

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("loomi")
        assert isinstance(session, LoomiSession)

        result = session.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, LoomiResult)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Human)
        assert node.name == "John"

        session.close()

    def test_session_partially_resolves_entities(self, sync_driver: Driver):
        """Verify that only registered models get transformed."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiClient(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            assert isinstance(session, LoomiSession)

            result = session.run(
                "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l, 'value'"
            )
            assert isinstance(result, LoomiResult)

            data = result.values()
            assert isinstance(data, list)

            animal = data[0][0]
            assert isinstance(animal, Human)
            assert animal.name == "John"

            animal = data[0][1]
            assert isinstance(animal, Node)
            assert animal.labels == {"Animal"}

            animal_properties = dict(animal)
            assert "kind" in animal_properties
            assert animal_properties["kind"] == "dog"

            owns = data[0][2]
            assert isinstance(owns, Owns)

            loves = data[0][3]
            assert isinstance(loves, Relationship)
            assert loves.type == "LOVES"

            primitive = data[0][4]
            assert isinstance(primitive, str)
            assert primitive == "value"


class TestLoomiTransaction:
    def test_transaction_works_with_context_manager(self, sync_driver: Driver):
        """
        Verify that the transaction behaves like the original transaction with transformation
        when used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            assert isinstance(session, LoomiSession)

            with session.begin_transaction() as tx:
                assert isinstance(tx, LoomiTransaction)

                tx.run("CREATE (:Human {name: $name})", {"name": "John"})

                result = tx.run("MATCH (n:Human) RETURN n")
                assert isinstance(result, LoomiResult)

                data = result.value()
                assert isinstance(data, list)

                node = data[0]
                assert isinstance(node, Human)
                assert node.name == "John"

    def test_transaction_works_with_manual_management(self, sync_driver: Driver):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when transaction is managed manually.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        session = client.session("loomi")
        assert isinstance(session, LoomiSession)

        tx = session.begin_transaction()
        assert isinstance(tx, LoomiTransaction)

        tx.run("CREATE (:Human {name: $name})", {"name": "John"})

        result = tx.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, LoomiResult)

        data = result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Human)
        assert node.name == "John"

        tx.commit()
        tx.close()
        session.close()

    def test_transaction_partially_resolves_entities(self, sync_driver: Driver):
        """Verify that only registered models get transformed."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiClient(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            with session.begin_transaction() as tx:
                assert isinstance(tx, LoomiTransaction)

                result = tx.run(
                    "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l, 'value'"
                )
                assert isinstance(result, LoomiResult)

                data = result.values()
                assert isinstance(data, list)

                animal = data[0][0]
                assert isinstance(animal, Human)
                assert animal.name == "John"

                animal = data[0][1]
                assert isinstance(animal, Node)
                assert animal.labels == {"Animal"}

                animal_properties = dict(animal)
                assert "kind" in animal_properties
                assert animal_properties["kind"] == "dog"

                owns = data[0][2]
                assert isinstance(owns, Owns)

                loves = data[0][3]
                assert isinstance(loves, Relationship)
                assert loves.type == "LOVES"

                primitive = data[0][4]
                assert isinstance(primitive, str)
                assert primitive == "value"


class TestNativeResult:
    def test_keeps_original_records_from_peek(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.peek()
            assert data is not None
            assert isinstance(data[0], Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    def test_keeps_original_records_from_fetch(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    def test_keeps_original_records_from_to_eager_result(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.to_eager_result()
            assert isinstance(data, EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], Node)

            properties = dict(data.records[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    def test_keeps_original_records_from_single(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.single()
            assert data is not None
            assert isinstance(data[0], Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    def test_keeps_original_records_from_values(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    def test_keeps_original_records_from_value(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.value()
            assert len(data) == 1
            assert isinstance(data[0], Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    def test_keeps_original_records_from_graph(self, sync_driver: Driver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.graph()
            assert isinstance(data, Graph)


class TestLoomiResult:
    def test_transforms_records_from_peek(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.peek()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    def test_transforms_records_from_peek_with_no_result(self, sync_driver: Driver):
        """Verify that the method returns none if no results are returned."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"})

            data = result.peek()
            assert data is None

    def test_transforms_records_from_fetch(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    def test_transforms_records_from_to_eager_result(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.to_eager_result()
            assert isinstance(data, EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], Human)
            assert data.records[0][0].name == "John"

    def test_transforms_records_from_single(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.single()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    def test_transforms_records_from_single_with_no_result(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"})

            data = result.single()
            assert data is None

    def test_transforms_records_from_values(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    def test_transforms_records_from_value(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.value()
            assert len(data) == 1
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    def test_transforms_records_from_graph(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.graph()
            assert isinstance(data, LoomiGraph)

    def test_transforms_records_from_next(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = next(result)
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    def test_transforms_records_from_iter(self, sync_driver: Driver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            for data in result:
                assert isinstance(data[0], Human)
                assert data[0].name == "John"

    def test_exposes_original_result_for_non_transformed_methods(self, sync_driver: Driver):
        """Verify that other methods which do not return graph entities are still available."""

        class Human(LoomiNode):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.keys()
            assert isinstance(data, list)
            assert data == ["n"]


class PickledHuman(LoomiNode):
    name: str


class PickledOwns(LoomiRelationship): ...


class TestLoomiGraph:
    def test_graph_entities_are_transformed(self, sync_driver: Driver):
        """Verify that entities inside the graph are transformed."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiClient(sync_driver)
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
                if isinstance(node, Node):
                    assert node.labels == {"Animal"}

                    properties = dict(node)
                    assert "kind" in properties
                    assert properties["kind"] == "dog"
                else:
                    assert isinstance(node, Human)
                    assert node.name == "John"

            for relationship in graph.relationships:
                if isinstance(relationship, Relationship):
                    assert relationship.type == "LOVES"
                else:
                    assert isinstance(relationship, Owns)

            rel_type = graph.relationship_type("OWNS")
            assert rel_type == Owns

    def test_graph_can_be_pickled(self, sync_driver: Driver):
        """Verify that the graph can be pickled."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiClient(sync_driver)
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
            assert isinstance(loaded, LoomiGraph)


class TestLoomiPath:
    def test_entities_from_path_are_transformed(self, sync_driver: Driver):
        """Verify that any returned paths have their entities transformed to Loomi equivalents."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (h:Human {name: $name}), (a:Animal {kind: $kind}), (h)-[:OWNS]->(a)-[:FED_BY]->(h)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiClient(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH p=(:Human)-[:OWNS]->(:Animal)-[:FED_BY]->(:Human) RETURN p")
            data = result.value()
            path = data[0]

            assert isinstance(path, LoomiPath)
            assert isinstance(path.start_node, Human)
            assert path.start_node.name == "John"
            assert isinstance(path.end_node, Human)
            assert path.end_node.name == "John"

            for node in path.nodes:
                if isinstance(node, Node):
                    assert node.labels == {"Animal"}

                    properties = dict(node)
                    assert "kind" in properties
                    assert properties["kind"] == "dog"
                else:
                    assert isinstance(node, Human)
                    assert node.name == "John"

            for relationship in path.relationships:
                if isinstance(relationship, Relationship):
                    assert relationship.type == "FED_BY"
                else:
                    assert isinstance(relationship, Owns)

    def test_path_graph_is_transformed(self, sync_driver: Driver):
        """Verify that the graph inside the path is transformed."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (h:Human {name: $name}), (a:Animal {kind: $kind}), (h)-[:OWNS]->(a)-[:FED_BY]->(h)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiClient(sync_driver)
        client.register(Human, Owns)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH p=(:Human)-[:OWNS]->(:Animal)-[:FED_BY]->(:Human) RETURN p")
            data = result.value()
            path = data[0]
            assert isinstance(path, LoomiPath)

            graph = path.graph
            assert len(graph.nodes) == 2
            assert len(graph.relationships) == 2

            for node in graph.nodes:
                if isinstance(node, Node):
                    assert node.labels == {"Animal"}

                    properties = dict(node)
                    assert "kind" in properties
                    assert properties["kind"] == "dog"
                else:
                    assert isinstance(node, Human)
                    assert node.name == "John"

            for relationship in graph.relationships:
                if isinstance(relationship, Relationship):
                    assert relationship.type == "FED_BY"
                else:
                    assert isinstance(relationship, Owns)

            rel_type = graph.relationship_type("OWNS")
            assert rel_type == Owns
