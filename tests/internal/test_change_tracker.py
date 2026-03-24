# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from os import environ

import pytest
from neo4j import GraphDatabase

from loomi._internal._change_tracker import TrackingOperation
from loomi._sync.change_tracker import ChangeTracker
from loomi._sync.client import Client
from loomi.exceptions import ChangeTrackerError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class Human(Node):
    name: str
    age: int


class Likes(Relationship):
    scale: float


@pytest.fixture
def change_tracker():
    uri = environ.get("NEO4J_URI", None)
    user = environ.get("NEO4J_USER", None)
    pwd = environ.get("NEO4J_PWD", None)

    if not uri or not user or not pwd:
        pytest.skip("Missing environment variable for database connection.")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    client = Client(driver)
    client.initialize()

    with client.session() as session:
        tracker = ChangeTracker(session, client)
        yield tracker


class TestAdd:
    @pytest.mark.integration
    def test_add_starts_tracking_unsaved_node_as_added(self, change_tracker: ChangeTracker):
        """
        Verify that a unsaved node is correctly tracked.
        """
        human = Human(name="John", age=21)
        change_tracker.add(human)

        assert len(change_tracker._state[TrackingOperation.UPDATE]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0

        assert len(change_tracker._state[TrackingOperation.INSERT]["nodes"]) == 1
        assert id(human) in change_tracker._state[TrackingOperation.INSERT]["nodes"]
        assert change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human)][0] == human

    @pytest.mark.integration
    def test_add_starts_tracking_unsaved_relationship_as_added(self, change_tracker: ChangeTracker):
        """
        Verify that a unsaved relationship is correctly tracked.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.5)
        change_tracker.add(likes, human1, human2)

        assert len(change_tracker._state[TrackingOperation.UPDATE]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0

        assert len(change_tracker._state[TrackingOperation.INSERT]["nodes"]) == 2
        assert id(human1) in change_tracker._state[TrackingOperation.INSERT]["nodes"]
        assert change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human1)][0] == human1
        assert id(human2) in change_tracker._state[TrackingOperation.INSERT]["nodes"]
        assert change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human2)][0] == human2

        assert len(change_tracker._state[TrackingOperation.INSERT]["relationships"]) == 1
        assert id(likes) in change_tracker._state[TrackingOperation.INSERT]["relationships"]
        assert (
            change_tracker._state[TrackingOperation.INSERT]["relationships"][id(likes)][0] == likes
        )

        assert len(change_tracker._grouping_map) == 1
        assert id(likes) in change_tracker._grouping_map
        assert change_tracker._grouping_map[id(likes)] == (id(human1), id(human2))

    @pytest.mark.integration
    def test_tracks_start_node_as_update_if_already_saved(self, change_tracker: ChangeTracker):
        """
        Verify that the start node is tracked as UPDATE if already saved to the DB.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.5)

        human1._element_id = "element_id_1"
        change_tracker.add(likes, human1, human2)

        assert id(human1) in change_tracker._state[TrackingOperation.UPDATE]["nodes"]
        assert change_tracker._state[TrackingOperation.UPDATE]["nodes"][id(human1)][0] == human1

        assert id(human2) in change_tracker._state[TrackingOperation.INSERT]["nodes"]
        assert change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human2)][0] == human2

    @pytest.mark.integration
    def test_tracks_end_node_as_update_if_already_saved(self, change_tracker: ChangeTracker):
        """
        Verify that the end node is tracked as UPDATE if already saved to the DB.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=9.5)

        human2._element_id = "element_id_2"
        change_tracker.add(likes, human1, human2)

        assert id(human1) in change_tracker._state[TrackingOperation.INSERT]["nodes"]
        assert change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human1)][0] == human1

        assert id(human2) in change_tracker._state[TrackingOperation.UPDATE]["nodes"]
        assert change_tracker._state[TrackingOperation.UPDATE]["nodes"][id(human2)][0] == human2

    @pytest.mark.integration
    def test_raises_if_start_or_end_node_not_defined(self, change_tracker: ChangeTracker):
        """
        Verify that a error is thrown when either start or end nodes are omitted when starting to
        track a relationship.
        """
        likes = Likes(scale=9.5)

        with pytest.raises(ChangeTrackerError):
            change_tracker.add(likes)

    @pytest.mark.integration
    def test_does_not_require_start_or_end_nodes(self, change_tracker: ChangeTracker):
        """
        Verify that a saved relationship does not need to define a start or end node.
        """
        likes = Likes(scale=9.5)
        likes._element_id = "element_id_1"
        change_tracker.add(likes)

        assert len(change_tracker._state[TrackingOperation.UPDATE]["relationships"]) == 1
        assert id(likes) in change_tracker._state[TrackingOperation.UPDATE]["relationships"]
        assert (
            change_tracker._state[TrackingOperation.UPDATE]["relationships"][id(likes)][0] == likes
        )

    @pytest.mark.integration
    def test_does_nothing_if_already_tracked(self, change_tracker: ChangeTracker):
        """
        Verify that nothing is changed if the entity is already being tracked.
        """
        human = Human(name="John", age=21)
        change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )

        change_tracker.add(human)

        assert len(change_tracker._state[TrackingOperation.UPDATE]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.INSERT]["nodes"]) == 1
        assert id(human) in change_tracker._state[TrackingOperation.INSERT]["nodes"]
        assert change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human)][0] == human

    @pytest.mark.integration
    def test_removes_node_if_previously_tracked_as_remove(self, change_tracker: ChangeTracker):
        """
        Verify that the node is no longer tracked if it was previously being tracked with a
        DELETE operation.
        """
        human = Human(name="John", age=21)
        change_tracker._state[TrackingOperation.DELETE]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )

        change_tracker.add(human)

        assert len(change_tracker._state[TrackingOperation.INSERT]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.UPDATE]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0

    @pytest.mark.integration
    def test_promotes_node_to_update_if_previously_tracked_as_remove(
        self, change_tracker: ChangeTracker
    ):
        """
        Verify that the node is promoted to being tracked as UPDATE if it was previously being
        tracked with a DELETE operation.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id_1"
        change_tracker._state[TrackingOperation.DELETE]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )

        change_tracker.add(human)

        assert len(change_tracker._state[TrackingOperation.INSERT]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0

        assert len(change_tracker._state[TrackingOperation.UPDATE]["nodes"]) == 1
        assert id(human) in change_tracker._state[TrackingOperation.UPDATE]["nodes"]
        assert change_tracker._state[TrackingOperation.UPDATE]["nodes"][id(human)][0] == human

    @pytest.mark.integration
    def test_removes_relationship_if_previously_tracked_as_remove(
        self, change_tracker: ChangeTracker
    ):
        """
        Verify that the relationship is no longer tracked if it was previously being tracked with a
        DELETE operation.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=2.1)
        change_tracker._state[TrackingOperation.DELETE]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )

        change_tracker.add(likes, human1, human2)

        assert len(change_tracker._state[TrackingOperation.INSERT]["relationships"]) == 0
        assert len(change_tracker._state[TrackingOperation.UPDATE]["relationships"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["relationships"]) == 0

    @pytest.mark.integration
    def test_promotes_relationship_to_update_if_previously_tracked_as_remove(
        self, change_tracker: ChangeTracker
    ):
        """
        Verify that the relationship is promoted to being tracked as UPDATE if it was previously
        being tracked with a DELETE operation.
        """
        human1 = Human(name="John", age=21)
        human2 = Human(name="Jane", age=20)
        likes = Likes(scale=2.1)
        likes._element_id = "element_id_1"
        change_tracker._state[TrackingOperation.DELETE]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )

        change_tracker.add(likes, human1, human2)

        assert len(change_tracker._state[TrackingOperation.INSERT]["relationships"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["relationships"]) == 0

        assert len(change_tracker._state[TrackingOperation.UPDATE]["relationships"]) == 1
        assert id(likes) in change_tracker._state[TrackingOperation.UPDATE]["relationships"]
        assert (
            change_tracker._state[TrackingOperation.UPDATE]["relationships"][id(likes)][0] == likes
        )


class TestRemove:
    @pytest.mark.integration
    def test_raises_with_non_saved_non_tracked_entity(self, change_tracker: ChangeTracker):
        """
        Verify that a exception is throws if a non saved entity should be tracked as DELETE when
        it has not been tracked before.
        """
        human = Human(name="John", age=21)

        with pytest.raises(ChangeTrackerError):
            change_tracker.remove(human)

    @pytest.mark.integration
    def test_removes_node_from_tracker_if_not_saved(self, change_tracker: ChangeTracker):
        """
        Verify that unsaved nodes which are being tracked as INSERT are removed from the change
        tracker state instead of being promoted to some other operation.
        """
        human = Human(name="John", age=21)

        change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )
        change_tracker.remove(human)

        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0

    @pytest.mark.integration
    def test_removes_relationship_from_tracker_if_not_saved(self, change_tracker: ChangeTracker):
        """
        Verify that unsaved relationships which are being tracked as INSERT are removed from the
        change tracker state instead of being promoted to some other operation.
        """
        likes = Likes(scale=2.1)

        change_tracker._state[TrackingOperation.INSERT]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )
        change_tracker.remove(likes)

        assert len(change_tracker._state[TrackingOperation.DELETE]["relationships"]) == 0

    @pytest.mark.integration
    def test_node_is_tracked_as_delete(self, change_tracker: ChangeTracker):
        """
        Verify that saved nodes are tracked as DELETE if not added to the change tracker prior.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id_1"

        change_tracker.remove(human)

        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 1
        assert id(human) in change_tracker._state[TrackingOperation.DELETE]["nodes"]
        assert change_tracker._state[TrackingOperation.DELETE]["nodes"][id(human)][0] == human

    @pytest.mark.integration
    def test_relationship_is_tracked_as_delete(self, change_tracker: ChangeTracker):
        """
        Verify that saved relationships are tracked as DELETE if not added to the change tracker
        prior.
        """
        likes = Likes(scale=2.1)
        likes._element_id = "element_id_1"

        change_tracker.remove(likes)

        assert len(change_tracker._state[TrackingOperation.DELETE]["relationships"]) == 1
        assert id(likes) in change_tracker._state[TrackingOperation.DELETE]["relationships"]
        assert (
            change_tracker._state[TrackingOperation.DELETE]["relationships"][id(likes)][0] == likes
        )

    @pytest.mark.integration
    def test_node_is_promoted_to_delete_if_already_tracked(self, change_tracker: ChangeTracker):
        """
        Verify that saved nodes are promoted to DELETE if they have been previously tracked.
        """
        human = Human(name="John", age=21)
        human._element_id = "element_id_1"

        change_tracker._state[TrackingOperation.UPDATE]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )
        change_tracker.remove(human)

        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 1
        assert id(human) in change_tracker._state[TrackingOperation.DELETE]["nodes"]
        assert change_tracker._state[TrackingOperation.DELETE]["nodes"][id(human)][0] == human

    @pytest.mark.integration
    def test_relationship_is_promoted_to_delete_if_already_tracked(
        self, change_tracker: ChangeTracker
    ):
        """
        Verify that saved relationships are promoted to DELETE if they have been previously tracked.
        """
        likes = Likes(scale=2.1)
        likes._element_id = "element_id_1"

        change_tracker._state[TrackingOperation.UPDATE]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )
        change_tracker.remove(likes)

        assert len(change_tracker._state[TrackingOperation.DELETE]["relationships"]) == 1
        assert id(likes) in change_tracker._state[TrackingOperation.DELETE]["relationships"]
        assert (
            change_tracker._state[TrackingOperation.DELETE]["relationships"][id(likes)][0] == likes
        )


class TestClear:
    @pytest.mark.integration
    def test_clears_change_tracker(self, change_tracker: ChangeTracker):
        """
        Verify that all state is cleared.
        """
        human = Human(name="John", age=21)
        likes = Likes(scale=2.1)

        change_tracker._state[TrackingOperation.INSERT]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )
        change_tracker._state[TrackingOperation.UPDATE]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )
        change_tracker._state[TrackingOperation.DELETE]["nodes"][id(human)] = (
            human,
            human._compute_checksums(),
        )

        change_tracker._state[TrackingOperation.INSERT]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )
        change_tracker._state[TrackingOperation.UPDATE]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )
        change_tracker._state[TrackingOperation.DELETE]["relationships"][id(likes)] = (
            likes,
            likes._compute_checksums(),
        )

        change_tracker.clear()

        assert len(change_tracker._state[TrackingOperation.INSERT]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.UPDATE]["nodes"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["nodes"]) == 0

        assert len(change_tracker._state[TrackingOperation.INSERT]["relationships"]) == 0
        assert len(change_tracker._state[TrackingOperation.UPDATE]["relationships"]) == 0
        assert len(change_tracker._state[TrackingOperation.DELETE]["relationships"]) == 0
