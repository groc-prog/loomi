# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

import pytest
from neo4j import Driver

from loomi.client.sync_client import LoomiClient
from loomi.exceptions import ChangeTrackerError, ModelError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from tests.fixtures.db import DriverSpec, ServerName, driver_spec, sync_driver


class Human(LoomiNode):
    name: str
    age: int


class Likes(LoomiRelationship):
    scale: float


class TestChangeTrackerFlushNodes:
    def test_does_not_create_redundant_relationships(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker does not attempt to create relationships where start or end
        node are being deleted.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=2.1)

        client = LoomiClient(sync_driver)
        client.register(Human, Likes)
        client.initialize()

        with client.session() as session:
            session.change_tracker.add(likes, human1, human2)
            session.change_tracker.remove(human1)

            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[r]->() RETURN r")
            records = result.values()
            assert len(records) == 0

    def test_creates_tracked_nodes(self, sync_driver: Driver, driver_spec: DriverSpec):
        """
        Verify that the change tracker creates nodes in the database which are being tracked as
        INSERT.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session() as session:
            session.change_tracker.add(human1)
            session.change_tracker.add(human2)

            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (n:Human) RETURN n ORDER BY n.age ASC")
            records = result.values()

            assert len(records) == 2
            assert dict(records[0][0])["name"] == "Jane"
            assert dict(records[1][0])["name"] == "John"

    def test_updates_tracked_nodes(self, sync_driver: Driver, driver_spec: DriverSpec):
        """
        Verify that the change tracker updates nodes in the database which are being tracked as
        UPDATE.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)

        with sync_driver.session() as session:
            result = session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                },
            )
            ids = result.values()

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

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session() as session:
            human2.age = 40
            session.change_tracker.add(human1)
            session.change_tracker.add(human2)
            human1.age = 41

            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (n:Human) RETURN n ORDER BY n.name ASC")
            records = result.values()

            assert len(records) == 2
            assert dict(records[0][0])["name"] == "Jane"
            assert dict(records[0][0])["age"] == 20
            assert dict(records[1][0])["name"] == "John"
            assert dict(records[1][0])["age"] == 41

    def test_raises_if_updated_node_is_not_saved(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the element ID of a tracked node can not
        be accessed when compiling queries.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id"
        human._id = 0

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session() as session:
            session.change_tracker.add(human)
            human._element_id = None
            human._id = None

            with pytest.raises(ChangeTrackerError):
                session.change_tracker.flush()

    def test_raises_if_labels_are_not_defined_on_tracked_node(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the labels of a tracked node can not be
        accessed when compiling queries.
        """

        class Worker(LoomiNode): ...

        worker = Worker()

        client = LoomiClient(sync_driver)
        client.register(Worker)
        client.initialize()

        with client.session() as session:
            session.change_tracker.add(worker)
            Worker.loomi_config.pop("labels")

            with pytest.raises(ModelError):
                session.change_tracker.flush()

    def test_raises_if_hash_not_defined_on_tracked_node(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the hash of a tracked node can not be
        accessed when compiling queries.
        """

        class Worker(LoomiNode): ...

        worker = Worker()

        client = LoomiClient(sync_driver)
        client.register(Worker)
        client.initialize()

        with client.session() as session:
            session.change_tracker.add(worker)
            Worker._hash = None

            with pytest.raises(ModelError):
                session.change_tracker.flush()

    def test_deletes_tracked_nodes(self, sync_driver: Driver, driver_spec: DriverSpec):
        """
        Verify that the change tracker deletes nodes in the database which are being tracked as
        REMOVE.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)

        with sync_driver.session() as session:
            result = session.run(
                "CREATE (n1:Human) SET n1 = $human1 "
                "CREATE (n2:Human) SET n2 = $human2 "
                f"RETURN {'elementId(n1), id(n1), elementId(n2), id(n2)' if driver_spec.name == ServerName.NEO4J else 'id(n1), id(n2)'}",
                {
                    "human1": human1.model_dump(),
                    "human2": human2.model_dump(),
                },
            )
            ids = result.values()

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

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session() as session:
            session.change_tracker.remove(human1)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (n:Human) RETURN n ORDER BY n.name ASC")
            records = result.values()

            assert len(records) == 1
            assert dict(records[0][0])["name"] == "Jane"

    def test_raises_if_deleted_node_is_not_saved(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that the change tracker throws a error if the element ID of a tracked node can not
        be accessed when compiling queries.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id"
        human._id = 0

        client = LoomiClient(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session() as session:
            session.change_tracker.remove(human)
            human._element_id = None
            human._id = None

            with pytest.raises(ChangeTrackerError):
                session.change_tracker.flush()
