# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

from loomi._sync.client import Client
from tests.integration.fixtures.seed_data import Adult, Child, HasChild, seed_entities_sync


class TestSyncChangeTrackerAddsNodeResults:
    def test_sync_change_tracker_adds_node_results_from_peek(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.peek()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_fetch(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.fetch(1)

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_to_eager_result(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.to_eager_result()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_single(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.single()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_values(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.values()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_value(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.value()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_graph(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            result.graph()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_iter(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)

            for record in result:
                record.values()

            add_spy.assert_called_once_with(adult)

    def test_sync_change_tracker_adds_node_results_from_next(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        adult, *_ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
            next(result)

            add_spy.assert_called_once_with(adult)


class TestSyncChangeTrackerAddsRelationshipResults:
    def test_sync_change_tracker_adds_relationship_results_from_peek(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.peek()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_fetch(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.fetch(1)

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_to_eager_result(
        self, sync_driver, mocker
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.to_eager_result()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_single(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.single()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_values(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.values()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_value(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.value()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_graph(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            result.graph()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_iter(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)

            for record in result:
                record.values()

            add_spy.assert_called_once_with(has_child)

    def test_sync_change_tracker_adds_relationship_results_from_next(self, sync_driver, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        _, has_child, _ = seed_entities_sync(sync_driver)

        with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            next(result)

            add_spy.assert_called_once_with(has_child)
