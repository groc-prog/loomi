# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import neo4j
import pytest

from loomi._sync.change_tracker import ChangeTracker
from loomi._sync.client import Client
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
def sync_tracker_client(sync_driver: neo4j.Driver):
    """Provide an initialized client registered for the tracker test models."""
    client = Client(sync_driver)
    client.initialize()
    client.register(TrackerPerson, TrackerKnows)
    return client


@pytest.fixture
def sync_change_tracker(sync_driver: neo4j.Driver, sync_tracker_client):
    """Provide a tracker backed by the configured sync session fixture."""
    with sync_driver.session() as session:
        yield ChangeTracker(session, sync_tracker_client)


def get_tracker_person_count(sync_driver: neo4j.Driver) -> int:
    with sync_driver.session() as session:
        result = session.run("MATCH (person:TrackerPerson) RETURN person")
        return len(result.values())


def get_tracker_relationship_count(sync_driver: neo4j.Driver) -> int:
    with sync_driver.session() as session:
        result = session.run("MATCH ()-[relationship:TRACKER_KNOWS]->() RETURN relationship")
        return len(result.values())


def get_tracker_person_tags(sync_driver: neo4j.Driver) -> list[list[str] | None]:
    with sync_driver.session() as session:
        result = session.run(
            "MATCH (person:TrackerPerson) " + "RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in result.data()]


def get_tracker_relationship_history(
    sync_driver: neo4j.Driver,
) -> list[list[int] | None]:
    with sync_driver.session() as session:
        result = session.run(
            "MATCH ()-[relationship:TRACKER_KNOWS]->() RETURN relationship.history AS history"
        )
        return [record["history"] for record in result.data()]


def get_tracker_relationships(
    sync_driver: neo4j.Driver,
) -> list[tuple[list[str] | None, list[str] | None, list[int] | None]]:
    with sync_driver.session() as session:
        result = session.run(
            "MATCH (start:TrackerPerson)-[relationship:TRACKER_KNOWS]->(end:TrackerPerson) "
            "RETURN start.tags AS start_tags, end.tags AS end_tags, "
            "relationship.history AS history ORDER BY relationship.history[0]"
        )
        return [
            (record["start_tags"], record["end_tags"], record["history"])
            for record in result.data()
        ]


class TestSyncChangeTrackerAdd:
    def test_add_unsaved_node_inserts_it_when_flushed(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        node = TrackerPerson(name="Alice", tags=["tracked"])

        sync_change_tracker.add(node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["tracked"]]

    def test_add_persisted_node_updates_it_when_flushed(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.add(node)
        node.tags = ["after"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["after"]]

    def test_add_persisted_node_twice_applies_latest_change_once(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker, caplog
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.add(node)
        sync_change_tracker.add(node)
        node.tags = ["after"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["after"]]
        assert "Entity has already been added to the change tracker" in caplog.text

    def test_add_node_with_cleared_element_id_cancels_pending_delete(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.remove(node)
        node._element_id = None
        sync_change_tracker.add(node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["alice"]]

    def test_add_relationship_with_cleared_element_id_cancels_pending_delete(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.remove(relationship)
        relationship._element_id = None
        sync_change_tracker.add(relationship)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]

    def test_add_unsaved_relationship_without_end_node_raises_and_flushes_no_data(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        relationship = TrackerKnows(since=2024)
        start_node = TrackerPerson(name="Alice")

        with pytest.raises(ChangeTrackerError, match="Both start and end nodes have to be defined"):
            sync_change_tracker.add(relationship, start_node=start_node)

        sync_change_tracker.flush()
        assert get_tracker_person_count(sync_driver) == 0
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_unsaved_relationship_without_start_node_raises_and_flushes_no_data(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        relationship = TrackerKnows(since=2024)
        end_node = TrackerPerson(name="Bob")

        with pytest.raises(ChangeTrackerError, match="Both start and end nodes have to be defined"):
            sync_change_tracker.add(relationship, end_node=end_node)

        sync_change_tracker.flush()
        assert get_tracker_person_count(sync_driver) == 0
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_unsaved_relationship_without_endpoints_raises_and_flushes_no_data(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        relationship = TrackerKnows(since=2024)
        with pytest.raises(ChangeTrackerError, match="Both start and end nodes have to be defined"):
            sync_change_tracker.add(relationship)

        sync_change_tracker.flush()
        assert get_tracker_person_count(sync_driver) == 0
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_unsaved_relationship_inserts_relationship_and_both_endpoints(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        relationship = TrackerKnows(since=2024, history=[2024])
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])

        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]


class TestSyncChangeTrackerNodeDeleteEmptyFlush:
    def test_flush_with_no_pending_node_deletions_preserves_nodes(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")

        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["alice"]]


class TestSyncChangeTrackerTransactionFlush:
    def test_flush_on_transaction_persists_node_and_relationship_on_commit(
        self,
        sync_driver: neo4j.Driver,
        sync_tracker_client,
    ):
        with sync_driver.session() as session:
            transaction = session.begin_transaction()
            tracker = ChangeTracker(transaction, sync_tracker_client)
            start_node = TrackerPerson(name="Alice", tags=["start"])
            end_node = TrackerPerson(name="Bob", tags=["end"])
            relationship = TrackerKnows(since=2024, history=[2024])

            tracker.add(relationship, start_node, end_node)
            tracker.flush()

            node_result = transaction.run(
                "MATCH (person:TrackerPerson) RETURN count(person) AS count"
            )
            node_record = node_result.single()
            assert node_record is not None
            assert node_record["count"] == 2

            relationship_result = transaction.run(
                "MATCH ()-[relationship:TRACKER_KNOWS]->() " + "RETURN count(relationship) AS count"
            )
            relationship_record = relationship_result.single()
            assert relationship_record is not None
            assert relationship_record["count"] == 1

            transaction.commit()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]

    def test_flush_on_transaction_does_not_commit_before_caller_rolls_back(
        self,
        sync_driver: neo4j.Driver,
        sync_tracker_client,
    ):
        with sync_driver.session() as session:
            transaction = session.begin_transaction()
            tracker = ChangeTracker(transaction, sync_tracker_client)
            node = TrackerPerson(name="Alice", tags=["alice"])
            tracker.add(node)
            tracker.flush()

            result = transaction.run("MATCH (person:TrackerPerson) RETURN count(person) AS count")
            record = result.single()
            assert record is not None
            assert record["count"] == 1

            transaction.rollback()

        assert get_tracker_person_count(sync_driver) == 0


class TestSyncChangeTrackerNodeDelete:
    def test_remove_persisted_node_deletes_it_and_detaches_relationships(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['alice']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['bob']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        alice = (
            sync_tracker_client.query(TrackerPerson).where(TrackerPerson.name == "Alice").execute()
        )[0]

        sync_change_tracker.remove(alice)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["bob"]]
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_remove_multiple_persisted_nodes_deletes_all_of_them(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})
                CREATE (:TrackerPerson {name: 'Bob', tags: ['bob']})
                CREATE (:TrackerPerson {name: 'Charlie', tags: ['charlie']})
                """
            )
        nodes = sync_tracker_client.query(TrackerPerson).execute()

        for node in nodes:
            sync_change_tracker.remove(node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 0
        assert get_tracker_person_tags(sync_driver) == []

    def test_remove_node_after_adding_it_still_deletes_it(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.add(node)
        sync_change_tracker.remove(node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 0
        assert get_tracker_person_tags(sync_driver) == []

    def test_flush_rejects_deleted_node_missing_element_id_and_preserves_database(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.remove(node)
        node._element_id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["alice"]]


class TestSyncChangeTrackerRelationshipDelete:
    def test_remove_persisted_relationship_deletes_edge_and_preserves_endpoints(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.remove(relationship)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 0
        assert get_tracker_person_tags(sync_driver) == [["end"], ["start"]]

    def test_flush_rejects_deleted_relationship_missing_element_id(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.remove(relationship)
        relationship._element_id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationship_history(sync_driver) == [[2024]]

    def test_flush_rejects_deleted_relationship_missing_numeric_id(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.remove(relationship)
        relationship._id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationship_history(sync_driver) == [[2024]]

    def test_remove_relationship_after_adding_persisted_edge_deletes_it(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.add(relationship)
        sync_change_tracker.remove(relationship)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 0
        assert get_tracker_person_tags(sync_driver) == [["end"], ["start"]]

    def test_flush_rejects_deleted_node_missing_numeric_id_and_preserves_database(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['alice']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.remove(node)
        node._id = None

        with pytest.raises(ChangeTrackerError, match="has not been saved to the database"):
            sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["alice"]]


class TestSyncChangeTrackerAddRelationships:
    def test_add_unchanged_persisted_relationship_leaves_database_unchanged(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2024, history: [2024]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.add(relationship)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationship_history(sync_driver) == [[2024]]
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]

    def test_add_relationship_omits_edge_when_unsaved_start_endpoint_is_removed(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])
        relationship = TrackerKnows(since=2024, history=[2024])
        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.remove(start_node)

        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["end"]]
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_relationship_omits_edge_when_unsaved_end_endpoint_is_removed(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])
        relationship = TrackerKnows(since=2024, history=[2024])
        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.remove(end_node)

        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["start"]]
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_relationship_omits_edge_when_persisted_start_endpoint_is_removed(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['persisted-start']})")
        start_node = (sync_tracker_client.query(TrackerPerson).execute())[0]
        end_node = TrackerPerson(name="Bob", tags=["new-end"])
        relationship = TrackerKnows(since=2024, history=[2024])
        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.remove(start_node)

        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["new-end"]]
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_relationship_omits_edge_when_persisted_end_endpoint_is_removed(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Bob', tags: ['persisted-end']})")
        end_node = (sync_tracker_client.query(TrackerPerson).execute())[0]
        start_node = TrackerPerson(name="Alice", tags=["new-start"])
        relationship = TrackerKnows(since=2024, history=[2024])
        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.remove(end_node)

        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["new-start"]]
        assert get_tracker_relationship_count(sync_driver) == 0

    def test_add_unsaved_relationship_with_persisted_start_inserts_and_updates(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['persisted-start']})")
        start_node = (sync_tracker_client.query(TrackerPerson).execute())[0]
        end_node = TrackerPerson(name="Bob", tags=["inserted-end"])
        relationship = TrackerKnows(since=2024, history=[2024])

        sync_change_tracker.add(relationship, start_node, end_node)
        start_node.tags = ["updated-start"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["inserted-end"], ["updated-start"]]
        assert get_tracker_relationships(sync_driver) == [
            (["updated-start"], ["inserted-end"], [2024])
        ]

    def test_add_unsaved_relationship_reuses_previously_tracked_persisted_start(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        start_node = (sync_tracker_client.query(TrackerPerson).execute())[0]
        end_node = TrackerPerson(name="Bob", tags=["new-end"])
        relationship = TrackerKnows(since=2024, history=[2024])

        sync_change_tracker.add(start_node)
        start_node.tags = ["between"]
        sync_change_tracker.add(relationship, start_node, end_node)
        start_node.tags = ["after"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_person_tags(sync_driver) == [["after"], ["new-end"]]
        assert get_tracker_relationships(sync_driver) == [(["after"], ["new-end"], [2024])]

    def test_add_unsaved_relationship_with_persisted_end_inserts_and_updates(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Bob', tags: ['persisted-end']})")
        end_node = (sync_tracker_client.query(TrackerPerson).execute())[0]
        start_node = TrackerPerson(name="Alice", tags=["inserted-start"])
        relationship = TrackerKnows(since=2024, history=[2024])

        sync_change_tracker.add(relationship, start_node, end_node)
        end_node.tags = ["updated-end"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["inserted-start"], ["updated-end"]]
        assert get_tracker_relationships(sync_driver) == [
            (["inserted-start"], ["updated-end"], [2024])
        ]

    def test_add_unsaved_relationship_reuses_previously_tracked_persisted_end(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Bob', tags: ['before']})")
        end_node = (sync_tracker_client.query(TrackerPerson).execute())[0]
        start_node = TrackerPerson(name="Alice", tags=["new-start"])
        relationship = TrackerKnows(since=2024, history=[2024])

        sync_change_tracker.add(end_node)
        end_node.tags = ["between"]
        sync_change_tracker.add(relationship, start_node, end_node)
        end_node.tags = ["after"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_person_tags(sync_driver) == [["after"], ["new-start"]]
        assert get_tracker_relationships(sync_driver) == [(["new-start"], ["after"], [2024])]

    def test_add_unsaved_relationship_with_both_persisted_endpoints_inserts_relationship(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (:TrackerPerson {name: 'Bob', tags: ['end']})
                """
            )
        start_node, end_node = (
            sync_tracker_client.query(TrackerPerson).order_by("name", OrderBy.ASC).execute()
        )
        relationship = TrackerKnows(since=2024, history=[2024])

        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]

    def test_add_unsaved_self_relationship_inserts_one_endpoint_and_self_edge(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        node = TrackerPerson(name="Self", tags=["self"])
        relationship = TrackerKnows(since=2024, history=[2024])

        sync_change_tracker.add(relationship, node, node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["self"]]
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["self"], ["self"], [2024])]

    def test_add_persisted_relationship_updates_it_when_flushed(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2023, history: [2023]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.add(relationship)
        relationship.history = [2024]
        sync_change_tracker.flush()

        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationship_history(sync_driver) == [[2024]]
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]

    def test_add_duplicate_unsaved_node_persists_only_one_copy(
        self, sync_driver: neo4j.Driver, sync_change_tracker, caplog
    ):
        node = TrackerPerson(name="Alice", tags=["tracked"])

        sync_change_tracker.add(node)
        sync_change_tracker.add(node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert "Entity has already been added to the change tracker" in caplog.text
        assert get_tracker_person_tags(sync_driver) == [["tracked"]]

    def test_add_duplicate_unsaved_relationship_persists_only_one_copy(
        self, sync_driver: neo4j.Driver, sync_change_tracker, caplog
    ):
        relationship = TrackerKnows(since=2024, history=[2024])
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])

        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]
        assert "Entity has already been added to the change tracker" in caplog.text

    def test_add_distinct_relationships_reuses_persisted_endpoints(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        start_node = TrackerPerson(name="Alice")
        end_node = TrackerPerson(name="Bob")
        first_relationship = TrackerKnows(since=2023, history=[2023])
        second_relationship = TrackerKnows(since=2024, history=[2024])
        start_node.tags = ["start"]
        end_node.tags = ["end"]

        sync_change_tracker.add(first_relationship, start_node, end_node)
        sync_change_tracker.add(second_relationship, start_node, end_node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 2
        assert get_tracker_relationships(sync_driver) == [
            (["start"], ["end"], [2023]),
            (["start"], ["end"], [2024]),
        ]

    def test_add_duplicate_persisted_relationship_updates_it_once(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker, caplog
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2023, history: [2023]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.add(relationship)
        sync_change_tracker.add(relationship)
        relationship.history = [2024]
        sync_change_tracker.flush()

        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationship_history(sync_driver) == [[2024]]
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]
        assert "Entity has already been added to the change tracker" in caplog.text

    def test_add_after_removing_persisted_node_restores_update(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run("CREATE (:TrackerPerson {name: 'Alice', tags: ['before']})")
        node = (sync_tracker_client.query(TrackerPerson).execute())[0]

        sync_change_tracker.remove(node)
        sync_change_tracker.add(node)
        node.tags = ["after"]
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["after"]]

    def test_add_after_removing_persisted_relationship_restores_update(
        self, sync_driver: neo4j.Driver, sync_tracker_client, sync_change_tracker
    ):
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (alice:TrackerPerson {name: 'Alice', tags: ['start']})
                CREATE (bob:TrackerPerson {name: 'Bob', tags: ['end']})
                CREATE (alice)-[:TRACKER_KNOWS {since: 2023, history: [2023]}]->(bob)
                """
            )
        relationship = (sync_tracker_client.query(TrackerKnows).execute())[0]

        sync_change_tracker.remove(relationship)
        sync_change_tracker.add(relationship)
        relationship.history = [2024]
        sync_change_tracker.flush()

        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationship_history(sync_driver) == [[2024]]
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]

    def test_add_after_removing_unsaved_node_inserts_it_when_flushed(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        node = TrackerPerson(name="Alice", tags=["tracked"])

        sync_change_tracker.add(node)
        sync_change_tracker.remove(node)
        sync_change_tracker.add(node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 1
        assert get_tracker_person_tags(sync_driver) == [["tracked"]]

    def test_add_after_removing_unsaved_relationship_inserts_it_when_flushed(
        self, sync_driver: neo4j.Driver, sync_change_tracker
    ):
        relationship = TrackerKnows(since=2024, history=[2024])
        start_node = TrackerPerson(name="Alice", tags=["start"])
        end_node = TrackerPerson(name="Bob", tags=["end"])

        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.remove(relationship)
        sync_change_tracker.add(relationship, start_node, end_node)
        sync_change_tracker.flush()

        assert get_tracker_person_count(sync_driver) == 2
        assert get_tracker_relationship_count(sync_driver) == 1
        assert get_tracker_relationships(sync_driver) == [(["start"], ["end"], [2024])]
