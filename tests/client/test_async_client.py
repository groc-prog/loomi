# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, line-too-long

import pickle

from neo4j import AsyncDriver, AsyncResult, AsyncSession, AsyncTransaction, EagerResult
from neo4j.graph import Graph, Node, Relationship

from loomi.client._internal.result import LoomiAsyncResult
from loomi.client._internal.session import LoomiAsyncSession
from loomi.client._internal.transaction import LoomiAsyncTransaction
from loomi.client.async_client import LoomiAsyncClient
from loomi.models.graph import LoomiGraph
from loomi.models.node import LoomiNode
from loomi.models.path import LoomiPath
from loomi.models.relationship import LoomiRelationship
from tests.fixtures.db import async_driver


class TestNativeAsyncSession:
    async def test_session_works_with_context_manager(self, async_driver: AsyncDriver):
        """
        Verify that the session behaves like the original session without transformation when
        used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            assert isinstance(session, AsyncSession)

            result = await session.run("MATCH (n:Human) RETURN n")
            assert isinstance(result, AsyncResult)

            data = await result.value()
            assert isinstance(data, list)

            node = data[0]
            assert isinstance(node, Node)
            assert node.labels == {"Human"}

            properties = dict(node)
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_session_works_with_manual_management(self, async_driver: AsyncDriver):
        """
        Verify that the session behaves like the original session without transformation when
        session is managed manually.
        """

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        session = client.session("native")
        assert isinstance(session, AsyncSession)

        result = await session.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, AsyncResult)

        data = await result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Node)
        assert node.labels == {"Human"}

        properties = dict(node)
        assert "name" in properties
        assert properties["name"] == "John"

        await session.close()

    async def test_transaction_works_with_context_manager(self, async_driver: AsyncDriver):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            assert isinstance(session, AsyncSession)

            async with await session.begin_transaction() as tx:
                assert isinstance(tx, AsyncTransaction)

                await tx.run("CREATE (:Human {name: $name})", {"name": "John"})

                result = await tx.run("MATCH (n:Human) RETURN n")
                assert isinstance(result, AsyncResult)

                data = await result.value()
                assert isinstance(data, list)

                node = data[0]
                assert isinstance(node, Node)
                assert node.labels == {"Human"}

                properties = dict(node)
                assert "name" in properties
                assert properties["name"] == "John"

    async def test_transaction_works_with_manual_management(self, async_driver: AsyncDriver):
        """
        Verify that the transaction behaves like the original transaction without transformation
        when transaction is managed manually.
        """

        class Human(LoomiNode):
            name: str

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        session = client.session("native")
        assert isinstance(session, AsyncSession)

        tx = await session.begin_transaction()
        assert isinstance(tx, AsyncTransaction)

        await tx.run("CREATE (:Human {name: $name})", {"name": "John"})

        result = await tx.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, AsyncResult)

        data = await result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Node)
        assert node.labels == {"Human"}

        properties = dict(node)
        assert "name" in properties
        assert properties["name"] == "John"

        await tx.commit()
        await tx.close()
        await session.close()


class TestLoomiAsyncSession:
    async def test_session_works_with_context_manager(self, async_driver: AsyncDriver):
        """
        Verify that the session behaves like the original session with transformation when
        used with a context manager.
        """

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            assert isinstance(session, LoomiAsyncSession)

            result = await session.run("MATCH (n:Human) RETURN n")
            assert isinstance(result, LoomiAsyncResult)

            data = await result.value()
            assert isinstance(data, list)

            node = data[0]
            assert isinstance(node, Human)
            assert node.name == "John"

    async def test_session_works_with_manual_management(self, async_driver: AsyncDriver):
        """
        Verify that the session behaves like the original session with transformation when
        session is managed manually.
        """

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        session = client.session("loomi")
        assert isinstance(session, LoomiAsyncSession)

        result = await session.run("MATCH (n:Human) RETURN n")
        assert isinstance(result, LoomiAsyncResult)

        data = await result.value()
        assert isinstance(data, list)

        node = data[0]
        assert isinstance(node, Human)
        assert node.name == "John"

        await session.close()

    async def test_session_partially_resolves_entities(self, async_driver: AsyncDriver):
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
            assert isinstance(session, LoomiAsyncSession)

            result = await session.run(
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


class TestLoomiAsyncTransaction:
    async def test_transaction_works_with_context_manager(self, async_driver: AsyncDriver):
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

    async def test_transaction_works_with_manual_management(self, async_driver: AsyncDriver):
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

    async def test_transaction_partially_resolves_entities(self, async_driver: AsyncDriver):
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


class TestNativeAsyncResult:
    async def test_keeps_original_records_from_peek(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.peek()
            assert data is not None
            assert isinstance(data[0], Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_keeps_original_records_from_fetch(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_keeps_original_records_from_to_eager_result(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.to_eager_result()
            assert isinstance(data, EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], Node)

            properties = dict(data.records[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_keeps_original_records_from_single(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.single()
            assert data is not None
            assert isinstance(data[0], Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_keeps_original_records_from_values(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_keeps_original_records_from_value(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.value()
            assert len(data) == 1
            assert isinstance(data[0], Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    async def test_keeps_original_records_from_graph(self, async_driver: AsyncDriver):
        """Verify that the method returns the unchanged results."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.graph()
            assert isinstance(data, Graph)


class TestLoomiAsyncResult:
    async def test_transforms_records_from_peek(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.peek()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    async def test_transforms_records_from_peek_with_no_result(self, async_driver: AsyncDriver):
        """Verify that the method returns none if no results are returned."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"}
            )

            data = await result.peek()
            assert data is None

    async def test_transforms_records_from_fetch(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    async def test_transforms_records_from_to_eager_result(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.to_eager_result()
            assert isinstance(data, EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], Human)
            assert data.records[0][0].name == "John"

    async def test_transforms_records_from_single(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.single()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    async def test_transforms_records_from_single_with_no_result(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"}
            )

            data = await result.single()
            assert data is None

    async def test_transforms_records_from_values(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    async def test_transforms_records_from_value(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.value()
            assert len(data) == 1
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    async def test_transforms_records_from_graph(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.graph()
            assert isinstance(data, LoomiGraph)

    async def test_transforms_records_from_iter(self, async_driver: AsyncDriver):
        """Verify that the method transforms results to models."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await anext(result)
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    async def test_exposes_original_result_for_non_transformed_methods(
        self, async_driver: AsyncDriver
    ):
        """Verify that other methods which do not return graph entities are still available."""

        class Human(LoomiNode):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = result.keys()
            assert isinstance(data, list)
            assert data == ["n"]


class PickledHuman(LoomiNode):
    name: str


class PickledOwns(LoomiRelationship): ...


class TestLoomiGraph:
    async def test_graph_entities_are_transformed(self, async_driver: AsyncDriver):
        """Verify that entities inside the graph are transformed."""

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
            result = await session.run(
                "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l"
            )
            graph = await result.graph()
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

    async def test_graph_can_be_pickled(self, async_driver: AsyncDriver):
        """Verify that the graph can be pickled."""
        async with async_driver.session() as session:
            await session.run(
                "CREATE (n:Human {name: $name}), (m:Animal {kind: $kind}), (n)-[:OWNS]->(m), (n)-[:LOVES]->(m)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiAsyncClient(async_driver)
        client.register(PickledHuman, PickledOwns)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH (n:Human), (m:Animal), (n)-[o:OWNS]->(m), (n)-[l:LOVES]->(m) RETURN n, m, o, l"
            )
            graph = await result.graph()

            pickled = pickle.dumps(graph)
            assert isinstance(pickled, bytes)

            loaded = pickle.loads(pickled)
            assert isinstance(loaded, LoomiGraph)


class TestLoomiPath:
    async def test_entities_from_path_are_transformed(self, async_driver: AsyncDriver):
        """Verify that any returned paths have their entities transformed to Loomi equivalents."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        async with async_driver.session() as session:
            await session.run(
                "CREATE (h:Human {name: $name}), (a:Animal {kind: $kind}), (h)-[:OWNS]->(a)-[:FED_BY]->(h)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Owns)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH p=(:Human)-[:OWNS]->(:Animal)-[:FED_BY]->(:Human) RETURN p"
            )
            data = await result.value()
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

    async def test_path_graph_is_transformed(self, async_driver: AsyncDriver):
        """Verify that the graph inside the path is transformed."""

        class Human(LoomiNode):
            name: str

        class Owns(LoomiRelationship): ...

        async with async_driver.session() as session:
            await session.run(
                "CREATE (h:Human {name: $name}), (a:Animal {kind: $kind}), (h)-[:OWNS]->(a)-[:FED_BY]->(h)",
                {"name": "John", "kind": "dog"},
            )

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Owns)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH p=(:Human)-[:OWNS]->(:Animal)-[:FED_BY]->(:Human) RETURN p"
            )
            data = await result.value()
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
