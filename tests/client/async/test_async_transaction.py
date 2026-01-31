# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, line-too-long, unused-argument

from neo4j import AsyncDriver
from neo4j.graph import Node, Relationship

from loomi.client._internal.result import LoomiAsyncResult
from loomi.client._internal.session import LoomiAsyncSession
from loomi.client._internal.transaction import LoomiAsyncTransaction
from loomi.client.async_client import LoomiAsyncClient
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from tests.fixtures.db import DriverSpec, async_driver, driver_spec


class TestLoomiAsyncTransaction:
    async def test_transaction_works_with_context_manager(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the transaction behaves like the original transaction with transformation
        when used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            assert isinstance(session, LoomiAsyncSession)

            async with await session.begin_transaction() as tx:
                assert isinstance(tx, LoomiAsyncTransaction)

                await tx.run("CREATE (:Human {name: $name})", {"name": "John"})

                result = await tx.run("MATCH (n:Human) RETURN n")
                assert isinstance(result, LoomiAsyncResult)

                data = await result.value()
                assert isinstance(data, list)

                node = data[0]
                assert isinstance(node, Human)
                assert node.name == "John"

    async def test_transaction_works_with_manual_management(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when transaction is managed manually.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        session = client.session("loomi")
        assert isinstance(session, LoomiAsyncSession)

        tx = await session.begin_transaction()
        assert isinstance(tx, LoomiAsyncTransaction)

        await tx.run("CREATE (:Human {name: $name})", {"name": "John"})

        result = await tx.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, LoomiAsyncResult)

        data = await result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Human)
        assert node.name == "John"

        await tx.commit()
        await tx.close()
        await session.close()

    async def test_transaction_partially_resolves_entities(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that only registered models get transformed."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        async with async_driver.session() as session:
            await session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Owns)
        await client.initialize()

        async with client.session("loomi") as session:
            async with await session.begin_transaction() as tx:
                assert isinstance(tx, LoomiAsyncTransaction)

                result = await tx.run(
                    "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l"
                )
                assert isinstance(result, LoomiAsyncResult)

                data = await result.values()
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
