# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi._async.session import AsyncSession
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


class TestAsyncClientInitialize:
    async def test_initialize_sets_server_type_and_version_for_configured_driver(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver)

        await client.initialize()

        assert client.server_type() == driver_spec.name
        assert client._server_version is not None
        assert len(client._server_version) > 0

    async def test_initialize_raises_client_error_when_driver_connectivity_fails(self):
        driver = SimpleNamespace()
        driver.verify_connectivity = AsyncMock(side_effect=RuntimeError("boom"))
        driver.get_server_info = AsyncMock()

        client = AsyncClient(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            await client.initialize()

    async def test_initialize_raises_client_error_when_version_query_returns_no_data(self):
        class MockResult:
            async def value(self):
                return []

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_value, traceback):
                return None

            async def run(self, _query):
                return MockResult()

        driver = SimpleNamespace()
        driver.verify_connectivity = AsyncMock()
        driver.get_server_info = AsyncMock(return_value=SimpleNamespace(agent="Neo4j"))
        driver.session = lambda: MockSession()  # pylint: disable=unnecessary-lambda

        client = AsyncClient(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            await client.initialize()


class TestAsyncClientSession:
    async def test_session_returns_native_and_loomi_sessions_after_initialization(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()

        native_session = client.session(mode="native")
        loomi_session = client.session()

        assert isinstance(native_session, neo4j.AsyncSession)
        assert isinstance(loomi_session, AsyncSession)

    async def test_session_raises_client_error_before_client_is_initialized(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.session()


class TestAsyncClientRegistration:
    async def test_register_skips_invalid_model_and_continues_with_valid_models(
        self, async_driver: neo4j.AsyncDriver, caplog
    ):
        client = AsyncClient(async_driver)

        client.register(cast(Any, int), Person)

        assert "Invalid model" in caplog.text
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = await client.query(Person).execute()
        assert len(results) == 1
        assert isinstance(results[0], Person)

    async def test_relationship_type_to_model_returns_none_when_not_strict(
        self, async_driver: neo4j.AsyncDriver, caplog
    ):
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()

        assert client._relationship_type_to_model("UNREGISTERED") is None
        assert "No model with type UNREGISTERED registered" in caplog.text

    async def test_relationship_type_to_model_raises_when_strict(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()

        with pytest.raises(SerializationError, match="No model with type UNREGISTERED registered"):
            client._relationship_type_to_model("UNREGISTERED")


class TestAsyncClientQuery:
    async def test_query_where_filters_registered_nodes(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = await client.query(Person).where(Person.age >= 40).execute()

        assert {person.name for person in results} == {"Bob", "Charlie"}
        assert all(isinstance(person, Person) for person in results)

    async def test_query_returns_empty_list_when_no_match_is_found(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = await client.query(Person).where(Person.age > 100).execute()

        assert results == []

    async def test_query_returns_registered_relationship_models(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2024}]->(bob)
                """
            )

        relationships = await client.query(Knows).where(Knows.since >= 2024).execute()

        assert len(relationships) == 1
        assert isinstance(relationships[0], Knows)
        assert relationships[0].since == 2024

    async def test_query_returns_projected_records_using_transaction(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

            tx = await session.begin_transaction()
            results = await client.query(Person, transaction=tx).project({"name": "name"}).execute()
            await tx.commit()

        assert sorted(item["name"] for item in results) == ["Alice", "Bob"]

    async def test_query_order_by_accepts_field_order_mapping_for_nodes(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = await client.query(Person).order_by({Person.name: OrderBy.ASC}).execute()

        assert [person.name for person in results] == ["Alice", "Bob", "Charlie"]
        assert all(isinstance(person, Person) for person in results)

    async def test_query_order_by_accepts_field_name_for_nodes(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        results = await client.query(Person).order_by("name", OrderBy.ASC).execute()

        assert [person.name for person in results] == ["Alice", "Bob", "Charlie"]

    async def test_query_project_returns_selected_node_fields(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        results = (
            await client.query(Person)
            .project({"name": "person_name", "age": "person_age"})
            .execute()
        )

        assert {item["person_name"]: item["person_age"] for item in results} == {
            "Alice": 30,
            "Bob": 40,
        }

    async def test_query_order_by_accepts_field_descriptor_for_relationships(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2025}]->(charlie)
                """
            )

        results = await client.query(Knows).order_by(cast(Any, Knows.since), OrderBy.ASC).execute()

        assert [relationship.since for relationship in results] == [2023, 2025]
        assert all(isinstance(relationship, Knows) for relationship in results)

    async def test_query_project_returns_selected_relationship_fields(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                """
            )

        results = await client.query(Knows).project({"since": "relationship_since"}).execute()

        assert results == [{"relationship_since": 2023}]

    async def test_query_skip_skips_node_results(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = await client.query(Person).skip(1).execute()

        assert len(results) == 2
        assert all(isinstance(person, Person) for person in results)

    async def test_query_limit_limits_node_results(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 50, active: true})
                """
            )

        results = await client.query(Person).limit(1).execute()

        assert len(results) == 1
        assert isinstance(results[0], Person)

    async def test_query_skip_skips_relationship_results(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2025}]->(charlie)
                """
            )

        results = await client.query(Knows).skip(1).execute()

        assert len(results) == 1
        assert isinstance(results[0], Knows)

    async def test_query_limit_limits_relationship_results(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2025}]->(charlie)
                """
            )

        results = await client.query(Knows).limit(1).execute()

        assert len(results) == 1
        assert isinstance(results[0], Knows)

    async def test_query_raises_for_invalid_expression(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="Invalid expression found"):
            client.query(Person).where("not-a-compilable-expression")

    async def test_query_raises_for_invalid_order_by_field(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="is not a valid field to order by"):
            client.query(Person).order_by("missing_field")

    async def test_query_raises_for_negative_limit(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="limit must be a positive integer if defined"):
            client.query(Person).limit(-1)

    async def test_query_raises_for_negative_skip(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="skip must be a positive integer if defined"):
            client.query(Person).skip(-1)

    async def test_query_returns_native_nodes_when_model_is_not_registered(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = await client.query(Person).execute()

        assert len(results) == 1
        assert not isinstance(results[0], Person)
        assert isinstance(next(iter(results[0].values())), neo4j.graph.Node)


class TestAsyncClientDelete:
    async def test_delete_where_filters_node_deletions(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 20, active: true})
                """
            )

        result = await client.delete(Person).where(Person.active == False).execute()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN count(p) AS total")
            record = await values.single()
            assert record is not None
            count = record["total"]

        assert count == 2

    async def test_delete_where_filters_relationship_deletions(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2024}]->(charlie)
                """
            )

        result = await client.delete(Knows).where(Knows.since >= 2024).execute()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            record = await values.single()
            assert record is not None
            count = record["total"]

        assert count == 1

    async def test_delete_execute_removes_all_nodes_and_detaches_relationships(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2024}]->(bob)
                """
            )

        result = await client.delete(Person).execute()

        assert result.affected == 2
        assert len(result.affected_ids) == 2

        async with async_driver.session() as session:
            nodes = await session.run("MATCH (n) RETURN count(n) AS total")
            node_record = await nodes.single()
            assert node_record is not None
            node_count = node_record["total"]
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            relationship_record = await values.single()
            assert relationship_record is not None
            relationship_count = relationship_record["total"]

        assert node_count == 0
        assert relationship_count == 0

    async def test_delete_execute_removes_all_relationships(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2024}]->(charlie)
                """
            )

        result = await client.delete(Knows).execute()

        assert result.affected == 2
        assert len(result.affected_ids) == 2

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            relationship_record = await values.single()
            assert relationship_record is not None
            relationship_count = relationship_record["total"]
            nodes = await session.run("MATCH (p:Person) RETURN count(p) AS total")
            node_record = await nodes.single()
            assert node_record is not None
            node_count = node_record["total"]

        assert relationship_count == 0
        assert node_count == 3

    async def test_delete_execute_removes_nodes_using_transaction(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

            tx = await session.begin_transaction()
            result = await client.delete(Person, transaction=tx).execute()
            await tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN count(p) AS total")
            record = await values.single()
            assert record is not None
            node_count = record["total"]

        assert node_count == 0

    async def test_delete_execute_removes_relationships_using_transaction(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2024}]->(bob)
                """
            )

            tx = await session.begin_transaction()
            result = await client.delete(Knows, transaction=tx).execute()
            await tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN count(r) AS total")
            record = await values.single()
            assert record is not None
            relationship_count = record["total"]

        assert relationship_count == 0

    async def test_delete_where_rejects_invalid_expression(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="Invalid expression found"):
            client.delete(Person).where("not-a-compilable-expression")


class TestAsyncClientUpdate:
    async def test_update_where_filters_node_updates(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: false})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        result = await (
            client.update(Person).where(Person.age >= 40).set_(Person.active, True).execute()
        )

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN p.name AS name, p.active AS active")
            data = await values.data()

        assert {row["name"]: row["active"] for row in data} == {"Alice": False, "Bob": True}

    async def test_update_where_filters_relationship_updates(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2024}]->(charlie)
                """
            )

        result = await (
            client.update(Knows).where(Knows.since >= 2024).set_(Knows.since, 2025).execute()
        )

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = await values.data()

        assert sorted(row["since"] for row in data) == [2023, 2025]

    async def test_update_set_assigns_literal_to_node_field(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: true})
                """
            )

        result = await client.update(Person).set_(Person.active, False).execute()

        assert result.affected == 2

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN p.active AS active")
            data = await values.data()

        assert data == [{"active": False}, {"active": False}]

    async def test_update_set_assigns_literal_to_relationship_field(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (charlie:Person {name: 'Charlie', age: 50, active: true})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                CREATE (alice)-[:KNOWS {since: 2024}]->(charlie)
                """
            )

        result = await client.update(Knows).set_(Knows.since, 2025).execute()

        assert result.affected == 2

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = await values.data()

        assert data == [{"since": 2025}, {"since": 2025}]

    async def test_update_set_accepts_expression_for_node_field(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                """
            )

        result = await client.update(Person).set_(Person.age, Person.age + 10).execute()

        assert result.affected == 2

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN p.age AS age ORDER BY p.age")
            data = await values.data()

        assert data == [{"age": 40}, {"age": 50}]

    async def test_update_set_accepts_expression_for_relationship_field(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2023}]->(bob)
                """
            )

        result = await client.update(Knows).set_(Knows.since, Knows.since + 1).execute()

        assert result.affected == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = await values.data()

        assert data == [{"since": 2024}]

    async def test_update_set_accepts_database_function_for_node_field(
        self, async_driver: neo4j.AsyncDriver
    ):
        from loomi.query.functions.transformation import to_upper

        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                """
            )

        result = await client.update(Person).set_(Person.name, to_upper(Person.name)).execute()

        assert result.affected == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN p.name AS name")
            data = await values.data()

        assert data == [{"name": "ALICE"}]

    async def test_update_set_accepts_database_function_for_relationship_field(
        self, async_driver: neo4j.AsyncDriver
    ):
        from loomi.query.functions.transformation import to_upper

        class KnowsWithStatus(Relationship):
            status: str

            loomi_config = {"type": "KNOWS"}

        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, KnowsWithStatus)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {status: 'friend'}]->(bob)
                """
            )

        result = await (
            client.update(KnowsWithStatus)
            .set_(KnowsWithStatus.status, to_upper(KnowsWithStatus.status))
            .execute()
        )

        assert result.affected == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN r.status AS status")
            data = await values.data()

        assert data == [{"status": "FRIEND"}]

    async def test_update_set_overwrites_previous_value_for_same_node_field(
        self, async_driver: neo4j.AsyncDriver, caplog: pytest.LogCaptureFixture
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        result = await (
            client.update(Person).set_(Person.active, True).set_(Person.active, False).execute()
        )

        assert result.affected == 1
        assert "A set operation has already been defined" in caplog.text

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN p.active AS active")
            data = await values.data()

        assert data == [{"active": False}]

    async def test_update_set_rejects_field_from_different_model(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        with pytest.raises(QueryError, match="Expected a valid field of model Person"):
            client.update(Person).set_(Knows.since, 2025)

    async def test_update_execute_raises_when_no_fields_are_set(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="At least one update expression must be defined"):
            await client.update(Person).execute()

    async def test_update_updates_nodes_using_transaction(self, async_driver: neo4j.AsyncDriver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

            tx = await session.begin_transaction()
            result = await client.update(Person, transaction=tx).set_(Person.age, 31).execute()
            await tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH (p:Person) RETURN p.age AS age")
            data = await values.data()

        assert data == [{"age": 31}]

    async def test_update_updates_relationships_using_transaction(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (alice:Person {name: 'Alice', age: 30, active: true})
                CREATE (bob:Person {name: 'Bob', age: 40, active: false})
                CREATE (alice)-[:KNOWS {since: 2024}]->(bob)
                """
            )

            tx = await session.begin_transaction()
            result = await client.update(Knows, transaction=tx).set_(Knows.since, 2025).execute()
            await tx.commit()

        assert result.affected == 1
        assert len(result.affected_ids) == 1

        async with async_driver.session() as session:
            values = await session.run("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")
            data = await values.data()

        assert data == [{"since": 2025}]
