# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import Any, cast

import neo4j
import pytest

from loomi._sync.client import Client
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api.constants import OrderBy


class Person(Node):
    name: str
    age: int
    active: bool = True

    loomi_config = {"labels": {"Person"}}


class Knows(Relationship):
    since: int = 2023

    loomi_config = {"type": "KNOWS"}


class TestSyncClientQuery:
    def test_query_where_filters_registered_nodes(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = client.query(Person).where(Person.age >= 40).execute()

        assert {person.name for person in results} == {"Bob", "Charlie"}
        assert all(isinstance(person, Person) for person in results)

    def test_query_returns_empty_list_when_no_match_is_found(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = client.query(Person).where(Person.age > 100).execute()

        assert results == []

    def test_query_returns_registered_relationship_models(self, sync_driver: neo4j.Driver):
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

        relationships = client.query(Knows).where(Knows.since >= 2024).execute()

        assert len(relationships) == 1
        assert isinstance(relationships[0], Knows)
        assert relationships[0].since == 2024

    def test_query_returns_projected_records_using_transaction(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

            tx = session.begin_transaction()
            results = client.query(Person, transaction=tx).project({"name": "name"}).execute()
            tx.commit()

        assert sorted(item["name"] for item in results) == ["Alice", "Bob"]

    def test_query_order_by_accepts_field_order_mapping_for_nodes(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = client.query(Person).order_by({Person.name: OrderBy.ASC}).execute()

        assert [person.name for person in results] == ["Alice", "Bob", "Charlie"]
        assert all(isinstance(person, Person) for person in results)

    def test_query_order_by_accepts_field_name_for_nodes(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        results = client.query(Person).order_by("name", OrderBy.ASC).execute()

        assert [person.name for person in results] == ["Alice", "Bob", "Charlie"]

    def test_query_project_returns_selected_node_fields(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        results = (
            client.query(Person).project({"name": "person_name", "age": "person_age"}).execute()
        )

        assert {item["person_name"]: item["person_age"] for item in results} == {
            "Alice": 30,
            "Bob": 40,
        }

    def test_query_order_by_accepts_field_descriptor_for_relationships(
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
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2025}]->(charlie)
                """
            )

        results = client.query(Knows).order_by(cast(Any, Knows.since), OrderBy.ASC).execute()

        assert [relationship.since for relationship in results] == [2023, 2025]
        assert all(isinstance(relationship, Knows) for relationship in results)

    def test_query_project_returns_selected_relationship_fields(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person, Knows)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                """
            )

        results = client.query(Knows).project({"since": "relationship_since"}).execute()

        assert results == [{"relationship_since": 2023}]

    def test_query_skip_skips_node_results(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = client.query(Person).skip(1).execute()

        assert len(results) == 2
        assert all(isinstance(person, Person) for person in results)

    def test_query_limit_limits_node_results(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = client.query(Person).limit(1).execute()

        assert len(results) == 1
        assert isinstance(results[0], Person)

    def test_query_skip_skips_relationship_results(self, sync_driver: neo4j.Driver):
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
                CREATE (alice)-[:KNOWS {since: 2025}]->(charlie)
                """
            )

        results = client.query(Knows).skip(1).execute()

        assert len(results) == 1
        assert isinstance(results[0], Knows)

    def test_query_limit_limits_relationship_results(self, sync_driver: neo4j.Driver):
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
                CREATE (alice)-[:KNOWS {since: 2025}]->(charlie)
                """
            )

        results = client.query(Knows).limit(1).execute()

        assert len(results) == 1
        assert isinstance(results[0], Knows)

    def test_query_raises_for_invalid_expression(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="Invalid expression found"):
            client.query(Person).where("not-a-compilable-expression")

    def test_query_raises_for_invalid_order_by_field(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="is not a valid field to order by"):
            client.query(Person).order_by("missing_field")

    def test_query_raises_for_negative_limit(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="limit must be a positive integer if defined"):
            client.query(Person).limit(-1)

    def test_query_raises_for_negative_skip(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="skip must be a positive integer if defined"):
            client.query(Person).skip(-1)

    def test_query_returns_native_nodes_when_model_is_not_registered(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = client.query(Person).execute()

        assert len(results) == 1
        assert not isinstance(results[0], Person)
        assert isinstance(next(iter(results[0].values())), neo4j.graph.Node)
