# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

import pytest
from neo4j import AsyncDriver

from loomi.client.async_client import LoomiAsyncClient
from loomi.exceptions import ChangeTrackerError, ModelError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from tests.fixtures.db import DriverSpec, ServerName, async_driver, driver_spec


class Human(LoomiNode):
    name: str
    age: int


class Likes(LoomiRelationship):
    scale: float


class TestFlushSession:
    async def test_creates_tracked_nodes(self, async_driver: AsyncDriver, driver_spec: DriverSpec):
        """
        Verify that the change tracker creates nodes in the database which are being tracked as
        INSERT.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(human1)
            session.change_tracker.add(human2)

            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (n:Human) RETURN n ORDER BY n.age ASC")
            records = await result.values()

            assert len(records) == 2
            assert dict(records[0][0])["name"] == "Jane"
            assert dict(records[1][0])["name"] == "John"

    async def test_updates_tracked_nodes(self, async_driver: AsyncDriver, driver_spec: DriverSpec):
        """
        Verify that the change tracker updates nodes in the database which are being tracked as
        UPDATE.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session() as session:
            human2.age = 40
            session.change_tracker.add(human1)
            session.change_tracker.add(human2)
            human1.age = 41

            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (n:Human) RETURN n ORDER BY n.name ASC")
            records = await result.values()

            assert len(records) == 2
            assert dict(records[0][0])["name"] == "Jane"
            assert dict(records[0][0])["age"] == 20
            assert dict(records[1][0])["name"] == "John"
            assert dict(records[1][0])["age"] == 41

    async def test_raises_if_updated_node_is_not_saved(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the element ID of a tracked node can not
        be accessed when compiling queries.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id"
        human._id = 0

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(human)
            human._element_id = None
            human._id = None

            with pytest.raises(ChangeTrackerError):
                await session.change_tracker.flush()

    async def test_raises_if_labels_are_not_defined_on_tracked_node(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the labels of a tracked node can not be
        accessed when compiling queries.
        """

        class Worker(LoomiNode): ...

        worker = Worker()

        client = LoomiAsyncClient(async_driver)
        client.register(Worker)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(worker)
            Worker.loomi_config.pop("labels")

            with pytest.raises(ModelError):
                await session.change_tracker.flush()

    async def test_raises_if_hash_not_defined_on_tracked_node(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the hash of a tracked node can not be
        accessed when compiling queries.
        """

        class Worker(LoomiNode): ...

        worker = Worker()

        client = LoomiAsyncClient(async_driver)
        client.register(Worker)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(worker)
            Worker._hash = None

            with pytest.raises(ModelError):
                await session.change_tracker.flush()

    async def test_deletes_tracked_nodes(self, async_driver: AsyncDriver, driver_spec: DriverSpec):
        """
        Verify that the change tracker deletes nodes in the database which are being tracked as
        REMOVE.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.remove(human1)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (n:Human) RETURN n ORDER BY n.name ASC")
            records = await result.values()

            assert len(records) == 1
            assert dict(records[0][0])["name"] == "Jane"

    async def test_raises_if_deleted_node_is_not_saved(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the element ID of a tracked node can not
        be accessed when compiling queries.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id"
        human._id = 0

        client = LoomiAsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.remove(human)
            human._element_id = None
            human._id = None

            with pytest.raises(ChangeTrackerError):
                await session.change_tracker.flush()

    async def test_does_not_create_redundant_relationships(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker does not attempt to create relationships where start or end
        node are being deleted.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=2.1)

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(likes, human1, human2)
            session.change_tracker.remove(human1)

            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[r]->() RETURN r")
            records = await result.values()
            assert len(records) == 0

    async def test_creates_tracked_relationships(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker creates relationships in the database which are being tracked as
        INSERT.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes1 = Likes(scale=9.2)
        likes2 = Likes(scale=3.8)

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(likes1, human1, human2)
            session.change_tracker.add(likes2, human2, human1)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (:Human)-[r:LIKES]->(:Human) RETURN r ORDER BY r.scale ASC"
            )
            records = await result.values()

            assert len(records) == 2
            assert dict(records[0][0])["scale"] == 3.8
            assert dict(records[1][0])["scale"] == 9.2

    async def test_raises_if_hash_not_defined_on_tracked_relationship(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the hash of a tracked relationship can not be
        accessed when compiling queries.
        """

        class Loves(LoomiRelationship): ...

        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        loves = Loves()

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Loves)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(loves, human1, human2)
            Loves._hash = None

            with pytest.raises(ModelError):
                await session.change_tracker.flush()

    async def test_raises_if_type_not_defined_on_tracked_relationship(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the type of a tracked relationship can not be
        accessed when compiling queries.
        """

        class Loves(LoomiRelationship): ...

        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        loves = Loves()

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Loves)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(loves, human1, human2)
            Loves.loomi_config.pop("type")

            with pytest.raises(ModelError):
                await session.change_tracker.flush()

    async def test_raises_if_start_node_tracked_with_inconsistent_state(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the start node of a tracked relationship is being
        tracked as UPDATE but has not been saved to the database.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.2)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(likes, human1, human2)
            human1._element_id = None
            human1._id = None

            with pytest.raises(ChangeTrackerError):
                await session.change_tracker.flush()

    async def test_raises_if_end_node_tracked_with_inconsistent_state(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the end node of a tracked relationship is being
        tracked as UPDATE but has not been saved to the database.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.2)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(likes, human1, human2)
            human2._element_id = None
            human2._id = None

            with pytest.raises(ChangeTrackerError):
                await session.change_tracker.flush()

    async def test_updates_tracked_relationships(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker updates relationships in the database which are being tracked as
        UPDATE.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes1 = Likes(scale=9.2)
        likes2 = Likes(scale=3.8)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                "CREATE (n1)-[r1:LIKES]->(n2) SET r1 = $likes1 "
                "CREATE (n2)-[r2:LIKES]->(n1) SET r2 = $likes2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2), elementId(r1), id(r1), elementId(r2), id(r2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2), id(r1), id(r2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                    "likes1": likes1.model_dump(),
                    "likes2": likes2.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
                likes1._element_id = ids[0][4]
                likes1._id = ids[0][5]
                likes2._element_id = ids[0][6]
                likes2._id = ids[0][7]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]
                likes1._element_id = str(ids[0][2])
                likes1._id = ids[0][2]
                likes2._element_id = str(ids[0][3])
                likes2._id = ids[0][3]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            likes2.scale = 10
            session.change_tracker.add(likes1, human1, human2)
            session.change_tracker.add(likes2, human2, human1)
            likes1.scale = 5.5

            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (:Human)-[r:LIKES]->(:Human) RETURN r ORDER BY r.scale ASC"
            )
            records = await result.values()

            assert len(records) == 2
            assert dict(records[0][0])["scale"] == 3.8
            assert dict(records[1][0])["scale"] == 5.5

    async def test_raises_if_updated_relationship_is_not_saved(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the element ID of a tracked relationship can not
        be accessed when compiling queries.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.2)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                "CREATE (n1)-[r1:LIKES]->(n2) SET r1 = $likes "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2), elementId(r1), id(r1)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2), id(r1)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                    "likes": likes.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
                likes._element_id = ids[0][4]
                likes._id = ids[0][5]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]
                likes._element_id = str(ids[0][2])
                likes._id = ids[0][2]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.add(likes, human1, human2)
            likes._element_id = None
            likes._id = None

            with pytest.raises(ChangeTrackerError):
                await session.change_tracker.flush()

    async def test_deletes_tracked_relationships(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker deletes relationships in the database which are being tracked as
        REMOVE.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes1 = Likes(scale=9.2)
        likes2 = Likes(scale=3.8)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                "CREATE (n1)-[r1:LIKES]->(n2) SET r1 = $likes1 "
                "CREATE (n2)-[r2:LIKES]->(n1) SET r2 = $likes2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2), elementId(r1), id(r1), elementId(r2), id(r2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2), id(r1), id(r2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                    "likes1": likes1.model_dump(),
                    "likes2": likes2.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
                likes1._element_id = ids[0][4]
                likes1._id = ids[0][5]
                likes2._element_id = ids[0][6]
                likes2._id = ids[0][7]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]
                likes1._element_id = str(ids[0][2])
                likes1._id = ids[0][2]
                likes2._element_id = str(ids[0][3])
                likes2._id = ids[0][3]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.remove(likes1)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (:Human)-[r:LIKES]->(:Human) RETURN r ORDER BY r.scale ASC"
            )
            records = await result.values()

            assert len(records) == 1
            assert dict(records[0][0])["scale"] == 3.8

    async def test_raises_if_deleted_relationship_is_not_saved(
        self, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the element ID of a tracked relationship can not
        be accessed when compiling queries.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.2)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                "CREATE (n1)-[r1:LIKES]->(n2) SET r1 = $likes1 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2), elementId(r1), id(r1)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2), id(r1)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                    "likes1": likes.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
                likes._element_id = ids[0][4]
                likes._id = ids[0][5]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]
                likes._element_id = str(ids[0][2])
                likes._id = ids[0][2]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            session.change_tracker.remove(likes)
            likes._element_id = None
            likes._id = None

            with pytest.raises(ChangeTrackerError):
                await session.change_tracker.flush()


class TestFlushTransaction:
    async def test_works_with_transaction(self, async_driver: AsyncDriver, driver_spec: DriverSpec):
        """
        Verify that the change tracker works when used with a transaction.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        human3 = Human(name="Jim", age=42)
        likes1 = Likes(scale=9.2)
        likes2 = Likes(scale=3.8)

        async with async_driver.session() as session:
            result = await session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                "CREATE (n1)-[r1:LIKES]->(n2) SET r1 = $likes1 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2), elementId(r1), id(r1)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2), id(r1)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                    "likes1": likes1.model_dump(),
                },
            )
            ids = await result.values()

            if driver_spec.name == ServerName.NEO4J:
                human1._element_id = ids[0][0]
                human1._id = ids[0][1]
                human2._element_id = ids[0][2]
                human2._id = ids[0][3]
                likes1._element_id = ids[0][4]
                likes1._id = ids[0][5]
            else:
                human1._element_id = str(ids[0][0])
                human1._id = ids[0][0]
                human2._element_id = str(ids[0][1])
                human2._id = ids[0][1]
                likes1._element_id = str(ids[0][2])
                likes1._id = ids[0][2]

        client = LoomiAsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                tx.change_tracker.add(likes1, human1, human2)
                tx.change_tracker.add(likes2, human2, human1)
                tx.change_tracker.add(human3)
                likes1.scale = 5.5
                human2.age = 18

                await tx.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (n:Human) RETURN n ORDER BY n.age ASC")
            records = await result.values()

            assert len(records) == 3
            assert dict(records[0][0])["name"] == "Jane"
            assert dict(records[1][0])["name"] == "John"
            assert dict(records[2][0])["name"] == "Jim"

            result = await session.run(
                "MATCH (:Human)-[r:LIKES]->(:Human) RETURN r ORDER BY r.scale ASC"
            )
            records = await result.values()

            assert len(records) == 2
            assert dict(records[0][0])["scale"] == 3.8
            assert dict(records[1][0])["scale"] == 5.5
