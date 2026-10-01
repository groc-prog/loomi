# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import neo4j
import pytest

from loomi._sync.client import Client
from loomi._sync.session import Session
from loomi.exceptions import ClientError, QueryError, SerializationError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query.constants import OrderBy
from tests.conftest import DriverSpec


class Person(Node):
    name: str
    age: int
    active: bool = True

    loomi_config = {"labels": {"Person"}}


class Knows(Relationship):
    since: int = 2023

    loomi_config = {"type": "KNOWS"}


class TestSyncClientInitialize:
    def test_initialize_sets_server_type_and_version_for_configured_driver(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver)

        client.initialize()

        assert client.server_type() == driver_spec.name
        assert client._server_version is not None
        assert len(client._server_version) > 0

    def test_initialize_raises_client_error_when_driver_connectivity_fails(self):
        driver = SimpleNamespace()
        driver.verify_connectivity = Mock(side_effect=RuntimeError("boom"))
        driver.get_server_info = Mock()

        client = Client(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            client.initialize()

    def test_initialize_raises_client_error_when_version_query_returns_no_data(self):
        class MockResult:
            def value(self):
                return []

        class MockSession:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def run(self, _query):
                return MockResult()

        driver = SimpleNamespace()
        driver.verify_connectivity = Mock()
        driver.get_server_info = Mock(return_value=SimpleNamespace(agent="Neo4j"))
        driver.session = lambda: MockSession()  # pylint: disable=unnecessary-lambda

        client = Client(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            client.initialize()


class TestSyncClientSession:
    def test_session_returns_native_and_loomi_sessions_after_initialization(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()

        native_session = client.session(mode="native")
        loomi_session = client.session()

        assert isinstance(native_session, neo4j.Session)
        assert isinstance(loomi_session, Session)

    def test_session_raises_client_error_before_client_is_initialized(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.session()


class TestSyncClientRegistration:
    def test_register_skips_invalid_model_and_continues_with_valid_models(
        self, sync_driver: neo4j.Driver, caplog
    ):
        client = Client(sync_driver)

        client.register(cast(Any, int), Person)

        assert "Invalid model" in caplog.text
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = client.query(Person).execute()
        assert len(results) == 1
        assert isinstance(results[0], Person)

    def test_relationship_type_to_model_returns_none_when_not_strict(
        self, sync_driver: neo4j.Driver, caplog
    ):
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()

        assert client._relationship_type_to_model("UNREGISTERED") is None
        assert "No model with type UNREGISTERED registered" in caplog.text

    def test_relationship_type_to_model_raises_when_strict(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()

        with pytest.raises(SerializationError, match="No model with type UNREGISTERED registered"):
            client._relationship_type_to_model("UNREGISTERED")


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


class TestSyncClientUpdate:
    def test_update_where_filters_node_updates(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: false})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        result = client.update(Person).where(Person.age >= 40).set_(Person.active, True).execute()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN p.name AS name, p.active AS active")
            data = values.data()

        assert {row["name"]: row["active"] for row in data} == {"Alice": False, "Bob": True}

    def test_update_where_filters_relationship_updates(self, sync_driver: neo4j.Driver):
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

        result = client.update(Knows).where(Knows.since >= 2024).set_(Knows.since, 2025).execute()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = values.data()

        assert sorted(row["since"] for row in data) == [2023, 2025]

    def test_update_set_assigns_literal_to_node_field(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: true})
                """
            )

        result = client.update(Person).set_(Person.active, False).execute()

        assert result.affected == 2

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN p.active AS active")
            data = values.data()

        assert data == [{"active": False}, {"active": False}]

    def test_update_set_assigns_literal_to_relationship_field(self, sync_driver: neo4j.Driver):
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

        result = client.update(Knows).set_(Knows.since, 2025).execute()

        assert result.affected == 2

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = values.data()

        assert data == [{"since": 2025}, {"since": 2025}]

    def test_update_set_accepts_expression_for_node_field(self, sync_driver: neo4j.Driver):
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

        result = client.update(Person).set_(Person.age, Person.age + 10).execute()

        assert result.affected == 2

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN p.age AS age ORDER BY p.age")
            data = values.data()

        assert data == [{"age": 40}, {"age": 50}]

    def test_update_set_accepts_expression_for_relationship_field(self, sync_driver: neo4j.Driver):
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

        result = client.update(Knows).set_(Knows.since, Knows.since + 1).execute()

        assert result.affected == 1

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = values.data()

        assert data == [{"since": 2024}]

    def test_update_set_accepts_database_function_for_node_field(self, sync_driver: neo4j.Driver):
        from loomi.query.functions.transformation import to_upper

        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                """
            )

        result = client.update(Person).set_(Person.name, to_upper(Person.name)).execute()

        assert result.affected == 1

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN p.name AS name")
            data = values.data()

        assert data == [{"name": "ALICE"}]

    def test_update_set_accepts_database_function_for_relationship_field(
        self, sync_driver: neo4j.Driver
    ):
        from loomi.query.functions.transformation import to_upper

        class KnowsWithStatus(Relationship):
            status: str

            loomi_config = {"type": "KNOWS"}

        client = Client(sync_driver)
        client.initialize()
        client.register(Person, KnowsWithStatus)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {status: 'friend'}]->(bob)
                """
            )

        result = (
            client.update(KnowsWithStatus)
            .set_(KnowsWithStatus.status, to_upper(KnowsWithStatus.status))
            .execute()
        )

        assert result.affected == 1

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN r.status AS status")
            data = values.data()

        assert data == [{"status": "FRIEND"}]

    def test_update_set_overwrites_previous_value_for_same_node_field(
        self, sync_driver: neo4j.Driver, caplog: pytest.LogCaptureFixture
    ):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        result = (
            client.update(Person).set_(Person.active, True).set_(Person.active, False).execute()
        )

        assert result.affected == 1
        assert "A set operation has already been defined" in caplog.text

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN p.active AS active")
            data = values.data()

        assert data == [{"active": False}]

    def test_update_set_rejects_field_from_different_model(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person, Knows)

        with pytest.raises(QueryError, match="Expected a valid field of model Person"):
            client.update(Person).set_(Knows.since, 2025)

    def test_update_execute_raises_when_no_fields_are_set(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="At least one update expression must be defined"):
            client.update(Person).execute()

    def test_update_updates_nodes_using_transaction(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

            tx = session.begin_transaction()
            result = client.update(Person, transaction=tx).set_(Person.age, 31).execute()
            tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH (p:Person) RETURN p.age AS age")
            data = values.data()

        assert data == [{"age": 31}]

    def test_update_updates_relationships_using_transaction(self, sync_driver: neo4j.Driver):
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
            result = client.update(Knows, transaction=tx).set_(Knows.since, 2025).execute()
            tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        with sync_driver.session() as session:
            values = session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = values.data()

        assert data == [{"since": 2025}]
