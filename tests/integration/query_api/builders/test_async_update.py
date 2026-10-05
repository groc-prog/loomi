# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import pytest

from loomi._async.client import AsyncClient
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


class TestAsyncClientUpdate:
    async def test_update_where_filters_node_updates(self, async_driver):
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

    async def test_update_where_filters_relationship_updates(self, async_driver):
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

    async def test_update_set_assigns_literal_to_node_field(self, async_driver):
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

    async def test_update_set_assigns_literal_to_relationship_field(self, async_driver):
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

    async def test_update_set_accepts_expression_for_node_field(self, async_driver):
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

    async def test_update_set_accepts_expression_for_relationship_field(self, async_driver):
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

    async def test_update_set_accepts_database_function_for_node_field(self, async_driver):
        from loomi.query_api.functions.transformation import to_upper

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

    async def test_update_set_accepts_database_function_for_relationship_field(self, async_driver):
        from loomi.query_api.functions.transformation import to_upper

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
        self, async_driver, caplog: pytest.LogCaptureFixture
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

    async def test_update_set_rejects_field_from_different_model(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person, Knows)

        with pytest.raises(QueryError, match="Expected a valid field of model Person"):
            client.update(Person).set_(Knows.since, 2025)

    async def test_update_execute_raises_when_no_fields_are_set(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="At least one update expression must be defined"):
            await client.update(Person).execute()

    async def test_update_updates_nodes_using_transaction(self, async_driver):
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

    async def test_update_updates_relationships_using_transaction(self, async_driver):
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
