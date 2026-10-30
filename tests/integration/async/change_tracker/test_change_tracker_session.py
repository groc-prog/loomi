# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi.exceptions import ChangeTrackerError
from tests.integration.fixtures.seed_data import (
    Adult,
    Child,
    HasChild,
    seed_entities_async,
    seed_start_and_end_nodes_async,
)


class TestAsyncChangeTrackerWithSession:
    async def test_async_change_tracker_with_session_add_with_session(self, async_driver, mocker):
        session_spy = mocker.spy(neo4j.AsyncSession, "begin_transaction")
        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            await session.change_tracker.flush()

        session_spy.assert_called_once()
        transaction_spy.assert_called_once()

    async def test_async_change_tracker_with_session_add_with_transaction(
        self, async_driver, mocker
    ):
        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                adult = Adult(name="John", age=21)
                tx.change_tracker.add(adult)
                await tx.change_tracker.flush()

        transaction_spy.assert_called_once()

    async def test_async_change_tracker_with_session_add_does_not_commit_transaction(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            async with await session.begin_transaction() as tx:
                adult = Adult(name="John", age=21)
                tx.change_tracker.add(adult)
                await tx.change_tracker.flush()
                await tx.rollback()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 0

    async def test_async_change_tracker_with_session_flush_clears_change_tracker(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")
        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            await session.change_tracker.flush()

            transaction_spy.assert_called()

            transaction_spy.reset_mock()
            await session.change_tracker.flush()
            transaction_spy.assert_not_called()


class TestAsyncChangeTrackerWithSessionAdd:
    async def test_async_change_tracker_with_session_add_creates_new_node(self, async_driver):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "John"
            assert entity["age"] == 21

    async def test_async_change_tracker_with_session_add_calling_add_multiple_times_on_unsaved_node_does_not_create_it_more_than_once(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            session.change_tracker.add(adult)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "John"
            assert entity["age"] == 21

    async def test_async_change_tracker_with_session_add_updates_changed_properties_on_existing_node(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.add(adult)
            adult.name = "Charles"
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "Charles"
            assert entity["age"] == 21

    async def test_async_change_tracker_with_session_add_readds_and_updates_node_after_being_marked_for_deletion(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.delete(adult)
            session.change_tracker.add(adult)
            adult.name = "Charles"
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "Charles"
            assert entity["age"] == 21

    async def test_async_change_tracker_with_session_add_does_not_update_changed_properties_on_existing_node_before_add_is_called(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            adult.name = "Charles"
            session.change_tracker.add(adult)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 1
            entity = values[0][0]

            assert entity["name"] == "John"
            assert entity["age"] == 21

    async def test_async_change_tracker_with_session_add_creates_new_relationship_with_unsaved_start_and_end_nodes(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = await result.values()

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

    async def test_async_change_tracker_with_session_add_creates_new_relationship_with_saved_start_and_end_nodes(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, child = await seed_start_and_end_nodes_async(async_driver)

        async with client.session() as session:
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = await result.values()

            assert len(values) == 1
            assert len(values[0]) == 3
            adult_entity = values[0][0]
            has_child_entity = values[0][1]
            child_entity = values[0][2]

            assert adult_entity.element_id == adult.element_id
            assert child_entity.element_id == child.element_id
            assert has_child_entity["nth_child"] == 1
            assert has_child_entity["tag"] == "oldest"

    async def test_async_change_tracker_with_session_add_raise_if_unsaved_relationship_is_passed_without_start_and_end_nodes(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            has_child = HasChild(nth_child=1, tag="oldest")

            with pytest.raises(
                ChangeTrackerError,
                match="Both start and end nodes have to be defined when tracking a unsaved relationship",
            ):
                session.change_tracker.add(has_child)

    async def test_async_change_tracker_with_session_add_calling_add_multiple_times_on_unsaved_relationship_and_start_and_end_nodes_does_not_create_it_more_than_once(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.add(has_child, adult, child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = await result.values()

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

    async def test_async_change_tracker_with_session_add_updates_changed_properties_on_existing_relationship(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.add(has_child)
            has_child.tag = "youngest"
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 1

            entity = values[0][0]

            assert entity["nth_child"] == 1
            assert entity["tag"] == "youngest"

    async def test_async_change_tracker_with_session_add_readds_and_updates_relationship_after_being_marked_for_deletion(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.delete(has_child)
            session.change_tracker.add(has_child)
            has_child.tag = "youngest"
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 1

            entity = values[0][0]

            assert entity["nth_child"] == 1
            assert entity["tag"] == "youngest"

    async def test_async_change_tracker_with_session_add_does_not_update_changed_properties_on_existing_relationship_before_add_is_called(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            has_child.tag = "youngest"
            session.change_tracker.add(has_child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 1

            entity = values[0][0]

            assert entity["nth_child"] == 1
            assert entity["tag"] == "oldest"


class TestAsyncChangeTrackerWithSessionDelete:
    async def test_async_change_tracker_with_session_delete_ignores_unsaved_node(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")
        async with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.delete(adult)
            await session.change_tracker.flush()

        transaction_spy.assert_not_called()

    async def test_async_change_tracker_with_session_delete_deletes_node(self, async_driver):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.delete(adult)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 0

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 1

    async def test_async_change_tracker_with_session_delete_calling_delete_on_saved_node_multiple_times_is_a_noop(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.delete(adult)
            session.change_tracker.delete(adult)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 0

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 1

    async def test_async_change_tracker_with_session_delete_deletes_node_previously_tracked_as_update(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.add(adult)
            session.change_tracker.delete(adult)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()

            assert len(values) == 0

    async def test_async_change_tracker_with_session_delete_ignores_unsaved_relationship(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")
        async with client.session() as session:
            has_child = HasChild(tag="oldest", nth_child=1)
            session.change_tracker.delete(has_child)
            await session.change_tracker.flush()

        transaction_spy.assert_not_called()

    async def test_async_change_tracker_with_session_delete_deletes_relationship(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.delete(has_child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 0

    async def test_async_change_tracker_with_session_delete_calling_delete_on_saved_relationship_multiple_times_is_a_noop(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)
        await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.delete(has_child)
            session.change_tracker.delete(has_child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 1
            assert values[0][0].element_id != has_child.element_id

            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 2

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 2

    async def test_async_change_tracker_with_session_delete_deletes_relationship_previously_tracked_as_update(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)
        await seed_entities_async(async_driver)

        async with client.session() as session:
            session.change_tracker.add(has_child)
            session.change_tracker.delete(has_child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 1
            assert values[0][0].element_id != has_child.element_id

            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 2

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 2

    async def test_async_change_tracker_with_session_delete_skips_relationship_creation_if_start_or_end_node_are_deleted(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.delete(child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = await result.values()
            assert len(values) == 0

            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 1

            adult_entity = values[0][0]
            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 0


class TestAsyncChangeTrackerWithSessionDetach:
    async def test_async_change_tracker_with_session_detach_stops_tracking_node(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")
        async with client.session() as session:
            adult = Adult(name="John", age=21)
            session.change_tracker.add(adult)
            session.change_tracker.detach(adult)
            await session.change_tracker.flush()

        transaction_spy.assert_not_called()

    async def test_async_change_tracker_with_session_detach_stops_tracking_relationship_but_not_start_and_end_nodes(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.detach(has_child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 0

            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 1

            adult_entity = values[0][0]
            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 1

            child_entity = values[0][0]
            assert child_entity["name"] == "Jimmy"

    async def test_async_change_tracker_with_session_detach_skips_relationship_creation_if_start_or_end_node_are_detached(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.detach(child)
            await session.change_tracker.flush()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult)-[b:HAS_CHILD]->(c:Child) RETURN a, b, c")
            values = await result.values()
            assert len(values) == 0

            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 1

            adult_entity = values[0][0]
            assert adult_entity["name"] == "John"
            assert adult_entity["age"] == 21

            result = await session.run("MATCH (a:Child) RETURN a")
            values = await result.values()
            assert len(values) == 0


class TestAsyncChangeTrackerWithSessionClear:
    async def test_async_change_tracker_with_session_clear_stops_tracking_all_entities(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        transaction_spy = mocker.spy(neo4j.AsyncTransaction, "run")
        async with client.session() as session:
            adult = Adult(name="John", age=21)
            child = Child(name="Jimmy")
            has_child = HasChild(nth_child=1, tag="oldest")
            session.change_tracker.add(has_child, adult, child)
            session.change_tracker.clear()
            await session.change_tracker.flush()

        transaction_spy.assert_not_called()
