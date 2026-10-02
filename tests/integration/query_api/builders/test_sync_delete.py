# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import neo4j
import pytest

from loomi._sync.client import Client
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class Person(Node):
    name: str
    age: int
    active: bool = True

    loomi_config = {"labels": {"Person"}}


class Knows(Relationship):
    since: int = 2023

    loomi_config = {"type": "KNOWS"}


class TestSyncClientDelete:
    def test_delete_where_filters_node_deletions(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 20, active: true})
                """
            )

        result = client.delete(Person).where(Person.active == False).execute()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN count(p) AS total")
            record = values.single()
            assert record is not None
            count = record["total"]

        assert count == 2

    def test_delete_where_filters_relationship_deletions(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person, Knows)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2024}]->(charlie)
                """
            )

        result = client.delete(Knows).where(Knows.since >= 2024).execute()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            record = values.single()
            assert record is not None
            count = record["total"]

        assert count == 1

    def test_delete_execute_removes_all_nodes_and_detaches_relationships(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person, Knows)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2024}]->(bob)
                """
            )

        result = client.delete(Person).execute()

        assert result.affected == 2
        assert len(result.affected_ids) == 2

        with sync_driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS total")
            node_record = nodes.single()
            assert node_record is not None
            node_count = node_record["total"]
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            relationship_record = values.single()
            assert relationship_record is not None
            relationship_count = relationship_record["total"]

        assert node_count == 0
        assert relationship_count == 0

    def test_delete_execute_removes_all_relationships(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person, Knows)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2024}]->(charlie)
                """
            )

        result = client.delete(Knows).execute()

        assert result.affected == 2
        assert len(result.affected_ids) == 2

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            relationship_record = values.single()
            assert relationship_record is not None
            relationship_count = relationship_record["total"]
            nodes = session.run("MATCH (p:Person) RETURN count(p) AS total")
            node_record = nodes.single()
            assert node_record is not None
            node_count = node_record["total"]

        assert relationship_count == 0
        assert node_count == 3

    def test_delete_execute_removes_nodes_using_transaction(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

            tx = session.begin_transaction()
            result = client.delete(Person, transaction=tx).execute()
            tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN count(p) AS total")
            record = values.single()
            assert record is not None
            node_count = record["total"]

        assert node_count == 0

    def test_delete_execute_removes_relationships_using_transaction(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person, Knows)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2024}]->(bob)
                """
            )

            tx = session.begin_transaction()
            result = client.delete(Knows, transaction=tx).execute()
            tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            record = values.single()
            assert record is not None
            relationship_count = record["total"]

        assert relationship_count == 0

    def test_delete_where_rejects_invalid_expression(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="Invalid expression found"):
            client.delete(Person).where("not-a-compilable-expression")
