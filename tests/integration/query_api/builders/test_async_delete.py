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


class TestAsyncClientDelete:
    async def test_delete_where_filters_node_deletions(self, async_driver):
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

    async def test_delete_where_filters_relationship_deletions(self, async_driver):
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

    async def test_delete_execute_removes_all_nodes_and_detaches_relationships(self, async_driver):
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

    async def test_delete_execute_removes_all_relationships(self, async_driver):
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

    async def test_delete_execute_removes_nodes_using_transaction(self, async_driver):
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

    async def test_delete_execute_removes_relationships_using_transaction(self, async_driver):
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

    async def test_delete_where_rejects_invalid_expression(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(Person)

        with pytest.raises(QueryError, match="Invalid expression found"):
            client.delete(Person).where("not-a-compilable-expression")
