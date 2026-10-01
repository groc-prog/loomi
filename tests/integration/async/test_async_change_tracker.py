# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import neo4j
import pytest

from loomi._async.change_tracker import AsyncChangeTracker
from loomi._async.client import AsyncClient
from loomi.exceptions import ChangeTrackerError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query.constants import OrderBy


class TrackerPerson(Node):
    name: str
    tags: list[str] | None = None

    loomi_config = {"labels": {"TrackerPerson"}}


class TrackerKnows(Relationship):
    since: int = 2023
    history: list[int] | None = None

    loomi_config = {"type": "TRACKER_KNOWS"}


@pytest.fixture
async def async_tracker_client(async_driver: neo4j.AsyncDriver):
    """Provide an initialized client registered for the tracker test models."""
    client = AsyncClient(async_driver)
    await client.initialize()
    client.register(TrackerPerson, TrackerKnows)
    return client


@pytest.fixture
async def async_change_tracker(async_driver: neo4j.AsyncDriver, async_tracker_client):
    """Provide a tracker backed by the configured async session fixture."""
    async with async_driver.session() as session:
        yield AsyncChangeTracker(session, async_tracker_client)


async def get_tracker_person_count(async_driver: neo4j.AsyncDriver) -> int:
    async with async_driver.session() as session:
        result = await session.run("MATCH (person:TrackerPerson) RETURN person")
        return len(await result.values())


async def get_tracker_relationship_count(async_driver: neo4j.AsyncDriver) -> int:
    async with async_driver.session() as session:
        result = await session.run("MATCH ()-[relationship:TRACKER_KNOWS]->() RETURN relationship")
        return len(await result.values())


async def get_tracker_person_tags(async_driver: neo4j.AsyncDriver) -> list[list[str] | None]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH (person:TrackerPerson) " + "RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in await result.data()]


async def get_tracker_relationship_history(
    async_driver: neo4j.AsyncDriver,
) -> list[list[int] | None]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH ()-[relationship:TRACKER_KNOWS]->() RETURN relationship.history AS history"
        )
        return [record["history"] for record in await result.data()]


async def get_tracker_relationships(
    async_driver: neo4j.AsyncDriver,
) -> list[tuple[list[str] | None, list[str] | None, list[int] | None]]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH (start:TrackerPerson)-[relationship:TRACKER_KNOWS]->(end:TrackerPerson) "
            "RETURN start.tags AS start_tags, end.tags AS end_tags, "
            "relationship.history AS history ORDER BY relationship.history[0]"
        )
        return [
            (record["start_tags"], record["end_tags"], record["history"])
            for record in await result.data()
        ]


class TestAsyncChangeTrackerAdd:
    async def test_add_unsaved_node_inserts_it_when_flushed(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        node = TrackerPerson(name="Alice", tags=["tracked"])

        async_change_tracker.add(node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["tracked"]]

    async def test_add_persisted_node_updates_it_when_flushed(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.add(node)
        node.tags = ["after"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["after"]]

    async def test_add_persisted_node_twice_applies_latest_change_once(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker, caplog
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.add(node)
        async_change_tracker.add(node)
        node.tags = ["after"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["after"]]
        assert "Entity has already been added to the change tracker" in caplog.text

    async def test_add_node_with_cleared_element_id_cancels_pending_delete(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.remove(node)
        node._element_id = None
        async_change_tracker.add(node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["alice"]]

    async def test_add_relationship_with_cleared_element_id_cancels_pending_delete(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.remove(relationship)
        relationship._element_id = None
        async_change_tracker.add(relationship)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]

    async def test_add_unsaved_relationship_without_end_node_raises_and_flushes_no_data(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        relationship = TrackerKnows(since=2024)
        start_node = TrackerPerson(name="Alice")

        with pytest.raises(ChangeTrackerError, match="Both start and end nodes have to be defined"):
            async_change_tracker.add(relationship, start_node=start_node)

        await async_change_tracker.flush()
        assert await get_tracker_person_count(async_driver) == 0
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_unsaved_relationship_without_start_node_raises_and_flushes_no_data(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        relationship = TrackerKnows(since=2024)
        end_node = TrackerPerson(name="Bob")

        with pytest.raises(ChangeTrackerError, match="Both start and end nodes have to be defined"):
            async_change_tracker.add(relationship, end_node=end_node)

        await async_change_tracker.flush()
        assert await get_tracker_person_count(async_driver) == 0
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_unsaved_relationship_without_endpoints_raises_and_flushes_no_data(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        relationship = TrackerKnows(since=2024)
        with pytest.raises(ChangeTrackerError, match="Both start and end nodes have to be defined"):
            async_change_tracker.add(relationship)

        await async_change_tracker.flush()
        assert await get_tracker_person_count(async_driver) == 0
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_unsaved_relationship_inserts_relationship_and_both_endpoints(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        relationship = TrackerKnows(since=2024, history=[2024])
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])

        async_change_tracker.add(relationship, start_node, end_node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]


class TestAsyncChangeTrackerNodeDeleteEmptyFlush:
    async def test_flush_with_no_pending_node_deletions_preserves_nodes(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")

        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["alice"]]


class TestAsyncChangeTrackerTransactionFlush:
    async def test_flush_on_transaction_persists_node_and_relationship_on_commit(
        self,
        async_driver: neo4j.AsyncDriver,
        async_tracker_client,
    ):
        async with async_driver.session() as session:
            transaction = await session.begin_transaction()
            tracker = AsyncChangeTracker(transaction, async_tracker_client)
            start_node = TrackerPerson(name="Alice", tags=["start"])
            end_node = TrackerPerson(name="Bob", tags=["end"])
            relationship = TrackerKnows(since=2024, history=[2024])

            tracker.add(relationship, start_node, end_node)
            await tracker.flush()

            node_result = await transaction.run(
                "MATCH (person:TrackerPerson) RETURN count(person) AS count"
            )
            node_record = await node_result.single()
            assert node_record is not None
            assert node_record["count"] == 2

            relationship_result = await transaction.run(
                "MATCH ()-[relationship:TRACKER_KNOWS]->() " + "RETURN count(relationship) AS count"
            )
            relationship_record = await relationship_result.single()
            assert relationship_record is not None
            assert relationship_record["count"] == 1

            await transaction.commit()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]

    async def test_flush_on_transaction_does_not_commit_before_caller_rolls_back(
        self,
        async_driver: neo4j.AsyncDriver,
        async_tracker_client,
    ):
        async with async_driver.session() as session:
            transaction = await session.begin_transaction()
            tracker = AsyncChangeTracker(transaction, async_tracker_client)
            node = TrackerPerson(name="Alice", tags=["alice"])
            tracker.add(node)
            await tracker.flush()

            result = await transaction.run(
                "MATCH (person:TrackerPerson) RETURN count(person) AS count"
            )
            record = await result.single()
            assert record is not None
            assert record["count"] == 1

            await transaction.rollback()

        assert await get_tracker_person_count(async_driver) == 0


class TestAsyncChangeTrackerNodeDelete:
    async def test_remove_persisted_node_deletes_it_and_detaches_relationships(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['alice']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['bob']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        alice = (
            await async_tracker_client.query(TrackerPerson)
            .where(TrackerPerson.name == "Alice")
            .execute()
        )[0]

        async_change_tracker.remove(alice)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["bob"]]
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_remove_multiple_persisted_nodes_deletes_all_of_them(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})
                CREATE (:TrackerPerson {name: 'Bob', tags: ['bob']})
                CREATE (:TrackerPerson {name: 'Charlie', tags: ['charlie']})
                """
            )
        nodes = await async_tracker_client.query(TrackerPerson).execute()

        for node in nodes:
            async_change_tracker.remove(node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 0
        assert await get_tracker_person_tags(async_driver) == []

    async def test_remove_node_after_adding_it_still_deletes_it(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.add(node)
        async_change_tracker.remove(node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 0
        assert await get_tracker_person_tags(async_driver) == []

    async def test_flush_rejects_deleted_node_missing_element_id_and_preserves_database(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.remove(node)
        node._element_id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["alice"]]


class TestAsyncChangeTrackerRelationshipDelete:
    async def test_remove_persisted_relationship_deletes_edge_and_preserves_endpoints(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.remove(relationship)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 0
        assert await get_tracker_person_tags(async_driver) == [["end"], ["start"]]

    async def test_flush_rejects_deleted_relationship_missing_element_id(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.remove(relationship)
        relationship._element_id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationship_history(async_driver) == [[2024]]

    async def test_flush_rejects_deleted_relationship_missing_numeric_id(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.remove(relationship)
        relationship._id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationship_history(async_driver) == [[2024]]

    async def test_remove_relationship_after_adding_persisted_edge_deletes_it(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.add(relationship)
        async_change_tracker.remove(relationship)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 0
        assert await get_tracker_person_tags(async_driver) == [["end"], ["start"]]

    async def test_flush_rejects_deleted_node_missing_numeric_id_and_preserves_database(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.remove(node)
        node._id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["alice"]]


class TestAsyncChangeTrackerAddRelationships:
    async def test_add_unchanged_persisted_relationship_leaves_database_unchanged(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.add(relationship)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationship_history(async_driver) == [[2024]]
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]

    async def test_add_relationship_omits_edge_when_unsaved_start_endpoint_is_removed(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])
        relationship = TrackerKnows(since=2024, history=[2024])
        async_change_tracker.add(relationship, start_node, end_node)
        async_change_tracker.remove(start_node)

        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["end"]]
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_relationship_omits_edge_when_unsaved_end_endpoint_is_removed(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])
        relationship = TrackerKnows(since=2024, history=[2024])
        async_change_tracker.add(relationship, start_node, end_node)
        async_change_tracker.remove(end_node)

        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["start"]]
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_relationship_omits_edge_when_persisted_start_endpoint_is_removed(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['persisted-start']})")
        start_node = (await async_tracker_client.query(TrackerPerson).execute())[0]
        end_node = TrackerPerson(name="Bob", tags=["new-end"])
        relationship = TrackerKnows(since=2024, history=[2024])
        async_change_tracker.add(relationship, start_node, end_node)
        async_change_tracker.remove(start_node)

        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["new-end"]]
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_relationship_omits_edge_when_persisted_end_endpoint_is_removed(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Bob', tags: ['persisted-end']})")
        end_node = (await async_tracker_client.query(TrackerPerson).execute())[0]
        start_node = TrackerPerson(name="Alice", tags=["new-start"])
        relationship = TrackerKnows(since=2024, history=[2024])
        async_change_tracker.add(relationship, start_node, end_node)
        async_change_tracker.remove(end_node)

        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["new-start"]]
        assert await get_tracker_relationship_count(async_driver) == 0

    async def test_add_unsaved_relationship_with_persisted_start_inserts_and_updates(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['persisted-start']})")
        start_node = (await async_tracker_client.query(TrackerPerson).execute())[0]
        end_node = TrackerPerson(name="Bob", tags=["inserted-end"])
        relationship = TrackerKnows(since=2024, history=[2024])

        async_change_tracker.add(relationship, start_node, end_node)
        start_node.tags = ["updated-start"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["inserted-end"], ["updated-start"]]
        assert await get_tracker_relationships(async_driver) == [
            (["updated-start"], ["inserted-end"], [2024])
        ]

    async def test_add_unsaved_relationship_reuses_previously_tracked_persisted_start(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        start_node = (await async_tracker_client.query(TrackerPerson).execute())[0]
        end_node = TrackerPerson(name="Bob", tags=["new-end"])
        relationship = TrackerKnows(since=2024, history=[2024])

        async_change_tracker.add(start_node)
        start_node.tags = ["between"]
        async_change_tracker.add(relationship, start_node, end_node)
        start_node.tags = ["after"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_person_tags(async_driver) == [["after"], ["new-end"]]
        assert await get_tracker_relationships(async_driver) == [(["after"], ["new-end"], [2024])]

    async def test_add_unsaved_relationship_with_persisted_end_inserts_and_updates(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Bob', tags: ['persisted-end']})")
        end_node = (await async_tracker_client.query(TrackerPerson).execute())[0]
        start_node = TrackerPerson(name="Alice", tags=["inserted-start"])
        relationship = TrackerKnows(since=2024, history=[2024])

        async_change_tracker.add(relationship, start_node, end_node)
        end_node.tags = ["updated-end"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["inserted-start"], ["updated-end"]]
        assert await get_tracker_relationships(async_driver) == [
            (["inserted-start"], ["updated-end"], [2024])
        ]

    async def test_add_unsaved_relationship_reuses_previously_tracked_persisted_end(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Bob', tags: ['before']})")
        end_node = (await async_tracker_client.query(TrackerPerson).execute())[0]
        start_node = TrackerPerson(name="Alice", tags=["new-start"])
        relationship = TrackerKnows(since=2024, history=[2024])

        async_change_tracker.add(end_node)
        end_node.tags = ["between"]
        async_change_tracker.add(relationship, start_node, end_node)
        end_node.tags = ["after"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_person_tags(async_driver) == [["after"], ["new-start"]]
        assert await get_tracker_relationships(async_driver) == [(["new-start"], ["after"], [2024])]

    async def test_add_unsaved_relationship_with_both_persisted_endpoints_inserts_relationship(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (:TrackerPerson {name: 'Bob', tags: ['end']})
                """
            )
        start_node, end_node = await (
            async_tracker_client.query(TrackerPerson).order_by("name", OrderBy.ASC).execute()
        )
        relationship = TrackerKnows(since=2024, history=[2024])

        async_change_tracker.add(relationship, start_node, end_node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]

    async def test_add_unsaved_self_relationship_inserts_one_endpoint_and_self_edge(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        node = TrackerPerson(name="Self", tags=["self"])
        relationship = TrackerKnows(since=2024, history=[2024])

        async_change_tracker.add(relationship, node, node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["self"]]
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["self"], ["self"], [2024])]

    async def test_add_persisted_relationship_updates_it_when_flushed(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2023, history: [2023]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.add(relationship)
        relationship.history = [2024]
        await async_change_tracker.flush()

        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationship_history(async_driver) == [[2024]]
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]

    async def test_add_duplicate_unsaved_node_persists_only_one_copy(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker, caplog
    ):
        node = TrackerPerson(name="Alice", tags=["tracked"])

        async_change_tracker.add(node)
        async_change_tracker.add(node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert "Entity has already been added to the change tracker" in caplog.text
        assert await get_tracker_person_tags(async_driver) == [["tracked"]]

    async def test_add_duplicate_unsaved_relationship_persists_only_one_copy(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker, caplog
    ):
        relationship = TrackerKnows(since=2024, history=[2024])
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])

        async_change_tracker.add(relationship, start_node, end_node)
        async_change_tracker.add(relationship, start_node, end_node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]
        assert "Entity has already been added to the change tracker" in caplog.text

    async def test_add_distinct_relationships_reuses_persisted_endpoints(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        start_node = TrackerPerson(name="Alice")
        end_node = TrackerPerson(name="Bob")
        first_relationship = TrackerKnows(since=2023, history=[2023])
        second_relationship = TrackerKnows(since=2024, history=[2024])
        start_node.tags = ["start"]
        end_node.tags = ["end"]

        async_change_tracker.add(first_relationship, start_node, end_node)
        async_change_tracker.add(second_relationship, start_node, end_node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 2
        assert await get_tracker_relationships(async_driver) == [
            (["start"], ["end"], [2023]),
            (["start"], ["end"], [2024]),
        ]

    async def test_add_duplicate_persisted_relationship_updates_it_once(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker, caplog
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2023, history: [2023]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.add(relationship)
        async_change_tracker.add(relationship)
        relationship.history = [2024]
        await async_change_tracker.flush()

        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationship_history(async_driver) == [[2024]]
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]
        assert "Entity has already been added to the change tracker" in caplog.text

    async def test_add_after_removing_persisted_node_restores_update(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        node = (await async_tracker_client.query(TrackerPerson).execute())[0]

        async_change_tracker.remove(node)
        async_change_tracker.add(node)
        node.tags = ["after"]
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["after"]]

    async def test_add_after_removing_persisted_relationship_restores_update(
        self, async_driver: neo4j.AsyncDriver, async_tracker_client, async_change_tracker
    ):
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2023, history: [2023]}]->(bob)
                """
            )
        relationship = (await async_tracker_client.query(TrackerKnows).execute())[0]

        async_change_tracker.remove(relationship)
        async_change_tracker.add(relationship)
        relationship.history = [2024]
        await async_change_tracker.flush()

        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationship_history(async_driver) == [[2024]]
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]

    async def test_add_after_removing_unsaved_node_inserts_it_when_flushed(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        node = TrackerPerson(name="Alice", tags=["tracked"])

        async_change_tracker.add(node)
        async_change_tracker.remove(node)
        async_change_tracker.add(node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 1
        assert await get_tracker_person_tags(async_driver) == [["tracked"]]

    async def test_add_after_removing_unsaved_relationship_inserts_it_when_flushed(
        self, async_driver: neo4j.AsyncDriver, async_change_tracker
    ):
        relationship = TrackerKnows(since=2024, history=[2024])
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])

        async_change_tracker.add(relationship, start_node, end_node)
        async_change_tracker.remove(relationship)
        async_change_tracker.add(relationship, start_node, end_node)
        await async_change_tracker.flush()

        assert await get_tracker_person_count(async_driver) == 2
        assert await get_tracker_relationship_count(async_driver) == 1
        assert await get_tracker_relationships(async_driver) == [(["start"], ["end"], [2024])]
