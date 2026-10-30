# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._sync.client import Client
from loomi.exceptions import ChangeTrackerError
from tests.integration.fixtures.seed_data import (
    Adult,
    Child,
    HasChild,
    seed_entities_sync,
    seed_start_and_end_nodes_sync,
)


class TestSyncChangeTrackerWithSession:
    def test_sync_change_tracker_with_session_add_with_session(self, sync_driver, mocker):
        session_spy = mocker.spy(neo4j.Session, "begin_transaction")
        transaction_spy = mocker.spy(neo4j.Transaction, "run")

        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            session.change_tracker.flush()

        session_spy.assert_called_once()
        transaction_spy.assert_called_once()

    def test_sync_change_tracker_with_session_add_with_transaction(self, sync_driver, mocker):
        transaction_spy = mocker.spy(neo4j.Transaction, "run")

        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            with session.begin_transaction() as tx:
                adult = Adult(name="John", age=21)
                tx.change_tracker.add(adult)
                tx.change_tracker.flush()

        transaction_spy.assert_called_once()

    def test_sync_change_tracker_with_session_add_does_not_commit_transaction(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            with session.begin_transaction() as tx:
                adult = Adult(name="John", age=21)
                tx.change_tracker.add(adult)
                tx.change_tracker.flush()
                tx.rollback()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 0

    def test_sync_change_tracker_with_session_flush_clears_change_tracker(
        self, sync_driver, mocker
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        transaction_spy = mocker.spy(neo4j.Transaction, "run")
        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.flush()

            transaction_spy.assert_called()

            transaction_spy.reset_mock()
            session.change_tracker.flush()
            transaction_spy.assert_not_called()


class TestSyncChangeTrackerWithSessionAdd:
    def test_sync_change_tracker_with_session_add_creates_new_node(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "John"
            assert entity["age"] == 21

    def test_sync_change_tracker_with_session_add_calling_add_multiple_times_on_unsaved_node_does_not_create_it_more_than_once(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            session.change_tracker.add(adult)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "John"
            assert entity["age"] == 21

    def test_sync_change_tracker_with_session_add_updates_changed_properties_on_existing_node(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.add(adult)
            adult.name = "Charles"
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "Charles"
            assert entity["age"] == 21

    def test_sync_change_tracker_with_session_add_readds_and_updates_node_after_being_marked_for_deletion(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.delete(adult)
            session.change_tracker.add(adult)
            adult.name = "Charles"
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "Charles"
            assert entity["age"] == 21

    def test_sync_change_tracker_with_session_add_does_not_update_changed_properties_on_existing_node_before_add_is_called(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            adult.name = "Charles"
            session.change_tracker.add(adult)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "John"
            assert entity["age"] == 21

    def test_sync_change_tracker_with_session_add_creates_new_relationship_with_unsaved_start_and_end_nodes(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = result.values()

            assert len(values) == 1
            assert len(values[0]) == 3
            adult_entity = values[0][0]
            has_child_entity = values[0][1]
            child_entity = values[0][2]

            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21
            assert has_child_entity["nth_child"] == 1
            assert has_child_entity["tag"] == "oldest"
            assert child_entity["name"] == "Jimmy"

    def test_sync_change_tracker_with_session_add_creates_new_relationship_with_saved_start_and_end_nodes(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, child = seed_start_and_end_nodes_sync(sync_driver)

        with client.session() as session:
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = result.values()

            assert len(values) == 1
            assert len(values[0]) == 3
            adult_entity = values[0][0]
            has_child_entity = values[0][1]
            child_entity = values[0][2]

            assert adult_entity.element_id == adult.element_id
            assert child_entity.element_id == child.element_id
            assert has_child_entity["nth_child"] == 1
            assert has_child_entity["tag"] == "oldest"

    def test_sync_change_tracker_with_session_add_raise_if_unsaved_relationship_is_passed_without_start_and_end_nodes(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            has_child = HasChild(nth_child=1, tag="oldest")

            with pytest.raises(
                ChangeTrackerError,
                match="Both start and end nodes have to be defined when tracking a unsaved relationship",
            ):
                session.change_tracker.add(has_child)

    def test_sync_change_tracker_with_session_add_calling_add_multiple_times_on_unsaved_relationship_and_start_and_end_nodes_does_not_create_it_more_than_once(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = result.values()

            assert len(values) == 1
            assert len(values[0]) == 3
            adult_entity = values[0][0]
            has_child_entity = values[0][1]
            child_entity = values[0][2]

            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21
            assert has_child_entity["nth_child"] == 1
            assert has_child_entity["tag"] == "oldest"
            assert child_entity["name"] == "Jimmy"

    def test_sync_change_tracker_with_session_add_updates_changed_properties_on_existing_relationship(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.add(has_child)
            has_child.tag = "youngest"
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 1

            entity = values[0][0]

            assert entity["nth_child"] == 1
            assert entity["tag"] == "youngest"

    def test_sync_change_tracker_with_session_add_readds_and_updates_relationship_after_being_marked_for_deletion(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.delete(has_child)
            session.change_tracker.add(has_child)
            has_child.tag = "youngest"
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 1

            entity = values[0][0]

            assert entity["nth_child"] == 1
            assert entity["tag"] == "youngest"

    def test_sync_change_tracker_with_session_add_does_not_update_changed_properties_on_existing_relationship_before_add_is_called(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            has_child.tag = "youngest"
            session.change_tracker.add(has_child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 1

            entity = values[0][0]

            assert entity["nth_child"] == 1
            assert entity["tag"] == "oldest"


class TestSyncChangeTrackerWithSessionDelete:
    def test_sync_change_tracker_with_session_delete_ignores_unsaved_node(
        self, sync_driver, mocker
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        transaction_spy = mocker.spy(neo4j.Transaction, "run")
        with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.delete(adult)
            session.change_tracker.flush()

        transaction_spy.assert_not_called()

    def test_sync_change_tracker_with_session_delete_deletes_node(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.delete(adult)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 0

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 1

    def test_sync_change_tracker_with_session_delete_calling_delete_on_saved_node_multiple_times_is_a_noop(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.delete(adult)
            session.change_tracker.delete(adult)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 0

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 1

    def test_sync_change_tracker_with_session_delete_deletes_node_previously_tracked_as_update(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.add(adult)
            session.change_tracker.delete(adult)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()

            assert len(values) == 0

    def test_sync_change_tracker_with_session_delete_ignores_unsaved_relationship(
        self, sync_driver, mocker
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        transaction_spy = mocker.spy(neo4j.Transaction, "run")
        with client.session() as session:
            has_child = HasChild(tag="oldest", nth_child=1)
            session.change_tracker.delete(has_child)
            session.change_tracker.flush()

        transaction_spy.assert_not_called()

    def test_sync_change_tracker_with_session_delete_deletes_relationship(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.delete(has_child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 0

    def test_sync_change_tracker_with_session_delete_calling_delete_on_saved_relationship_multiple_times_is_a_noop(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)
        seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.delete(has_child)
            session.change_tracker.delete(has_child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 1
            assert values[0][0].element_id != has_child.element_id

            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 2

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 2

    def test_sync_change_tracker_with_session_delete_deletes_relationship_previously_tracked_as_update(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)
        seed_entities_sync(sync_driver)

        with client.session() as session:
            session.change_tracker.add(has_child)
            session.change_tracker.delete(has_child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 1
            assert values[0][0].element_id != has_child.element_id

            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 2

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 2

    def test_sync_change_tracker_with_session_delete_skips_relationship_creation_if_start_or_end_node_are_deleted(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.delete(child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = result.values()
            assert len(values) == 0

            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 1

            adult_entity = values[0][0]
            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 0


class TestSyncChangeTrackerWithSessionDetach:
    def test_sync_change_tracker_with_session_detach_stops_tracking_node(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        transaction_spy = mocker.spy(neo4j.Transaction, "run")
        with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            session.change_tracker.detach(adult)
            session.change_tracker.flush()

        transaction_spy.assert_not_called()

    def test_sync_change_tracker_with_session_detach_stops_tracking_relationship_but_not_start_and_end_nodes(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.detach(has_child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 0

            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 1

            adult_entity = values[0][0]
            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 1

            child_entity = values[0][0]
            assert child_entity["name"] == "Jimmy"

    def test_sync_change_tracker_with_session_detach_skips_relationship_creation_if_start_or_end_node_are_detached(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.detach(child)
            session.change_tracker.flush()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = result.values()
            assert len(values) == 0

            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 1

            adult_entity = values[0][0]
            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21

            result = session.run("MATCH (a:Child) RETURN a")
            values = result.values()
            assert len(values) == 0


class TestSyncChangeTrackerWithSessionClear:
    def test_sync_change_tracker_with_session_clear_stops_tracking_all_entities(
        self, sync_driver, mocker
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        transaction_spy = mocker.spy(neo4j.Transaction, "run")
        with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.clear()
            session.change_tracker.flush()

        transaction_spy.assert_not_called()
