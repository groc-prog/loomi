# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._sync.client import Client
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api._builders.update_builder import UpdateResult
from loomi.query_api._core.expressions import CompoundExpression
from loomi.query_api._core.protocols import CompilableExpression
from loomi.query_api.functions.comparison import (
    ends_with,
    equals,
    greater_than_or_equal,
    less_than_or_equal,
    or_,
    starts_with,
)
from loomi.query_api.functions.transformation import to_upper


class Adult(Node):
    name: str
    age: int

    loomi_config = {"labels": {"Adult"}}


class Child(Node):
    name: str

    loomi_config = {"labels": {"Child"}}


class HasChild(Relationship):
    nth_child: int
    kind: str

    loomi_config = {"type": "HAS_CHILD"}


@pytest.fixture
def seed_data(sync_driver):
    with sync_driver.session() as session:
        for i in range(5):
            session.run(
                "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c)",
                {
                    "a": {"name": f"Adult:{i}", "age": i},
                    "b": {"nth_child": i, "kind": "boy"},
                    "c": {"name": f"Child:{i}"},
                },
            )


class TestSyncClientUpdate:
    def test_sync_client_update_passes_kwargs_to_session(self, sync_driver, seed_data, mocker):
        session_spy = mocker.spy(neo4j.Session, "run")

        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        test_fetch_size = 1000

        session_spy.reset_mock()
        client.update(Adult, fetch_size=test_fetch_size).set("name", "update").execute()
        session_spy.assert_called_once_with(
            mocker.ANY, mocker.ANY, mocker.ANY, fetch_size=test_fetch_size
        )

    def test_sync_client_update_accepts_transaction(self, sync_driver, seed_data, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            with session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                client.update(Adult, tx).set("name", "update").execute()
                tx_run_spy.assert_called_once()
                session_run_spy.assert_not_called()

    def test_sync_client_update_passes_kwargs_to_transaction(self, sync_driver, seed_data, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        test_timeout = 10

        with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            with session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                client.update(Adult, tx, timeout=test_timeout).set("name", "update").execute()
                tx_run_spy.assert_called_once_with(mocker.ANY, mocker.ANY, timeout=test_timeout)
                session_run_spy.assert_not_called()

    def test_sync_client_update_raises_if_set_has_not_been_called(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="At least one update expression must be defined"):
            client.update(Adult).execute()


class TestSyncClientUpdateNodes:
    def test_sync_client_update_nodes_updates_all_nodes(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN id(a), elementId(a)")
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(Adult).set(Adult.name, "updated").execute()
        assert isinstance(result, UpdateResult)
        assert result.affected == 5

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"


class TestSyncClientUpdateNodesWhere:
    def test_sync_client_update_nodes_where_only_updates_filtered_entities(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN id(a), elementId(a)",
                {"name": "Adult:0"},
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(Adult)
            .where(ends_with(Adult.name, "0"))
            .set(Adult.name, "updated")
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN a", {"name": "updated"}
            )
            values = result.values()
            assert len(values) == 1

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    def test_sync_client_update_nodes_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN id(a), elementId(a)",
                {"name": "Adult:0"},
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(Adult)
            .where(starts_with(Adult.name, "Adult"))
            .where(ends_with(Adult.name, "0"))
            .set(Adult.name, "updated")
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN a", {"name": "updated"}
            )
            values = result.values()
            assert len(values) == 1

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    def test_sync_client_update_nodes_where_with_compound_filters(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) WHERE a.name = $name1 OR a.name = $name2 RETURN id(a), elementId(a)",
                {"name1": "Adult:0", "name2": "Adult:4"},
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(Adult)
            .where(or_(ends_with(Adult.name, "0"), ends_with(Adult.name, "4")))
            .set(Adult.name, "updated")
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN a", {"name": "updated"}
            )
            values = result.values()
            assert len(values) == 2

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    def test_sync_client_update_nodes_where_raises_if_invalid_expression_provided(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            client.update(Adult).where(2 == 2).set(Adult.name, "updated").execute()


class TestSyncClientUpdateNodesSet:
    def test_sync_client_update_nodes_set_with_descriptor(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(Adult).set(Adult.name, "updated").execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    def test_sync_client_update_nodes_set_with_field_name(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(Adult).set("name", "updated").execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    def test_sync_client_update_nodes_set_with_expression_value(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(Adult).set(Adult.age, Adult.age + 20).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["age"] >= 20

    def test_sync_client_update_nodes_set_with_db_function(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(Adult).set(Adult.name, to_upper(Adult.name)).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"].startswith("ADULT:")

    def test_sync_client_update_nodes_set_overwrites_field_update_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(Adult).set(Adult.name, "updated").set(Adult.name, "other").execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH (a:Adult) RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "other"

    def test_sync_client_update_nodes_set_raises_if_field_descriptor_is_for_wrong_model(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid field found. Expected a valid field of model {Adult.__name__}, got name",
        ):
            client.update(Adult).set(Child.name, "updated").execute()


class TestSyncClientUpdateRelationships:
    def test_sync_client_update_relationships_updates_all_relationships(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)")
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(HasChild).set(HasChild.nth_child, 10).execute()
        assert isinstance(result, UpdateResult)
        assert result.affected == 5

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10


class TestSyncClientUpdateRelationshipsWhere:
    def test_sync_client_update_relationships_where_only_updates_filtered_entities(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN id(a), elementId(a)",
                {"count": 0},
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(HasChild)
            .where(equals(HasChild.nth_child, 0))
            .set(HasChild.nth_child, 10)
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = result.values()
            assert len(values) == 1

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    def test_sync_client_update_relationships_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count1 OR a.nth_child = $count2 RETURN id(a), elementId(a)",
                {"count1": 0, "count2": 1},
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(HasChild)
            .where(greater_than_or_equal(HasChild.nth_child, 0))
            .where(less_than_or_equal(HasChild.nth_child, 1))
            .set(HasChild.nth_child, 10)
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = result.values()
            assert len(values) == 2

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    def test_sync_client_update_relationships_where_with_compound_filters(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count1 OR a.nth_child = $count2 RETURN id(a), elementId(a)",
                {"count1": 2, "count2": 3},
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(HasChild)
            .where(or_(equals(HasChild.nth_child, 2), equals(HasChild.nth_child, 3)))
            .set(HasChild.nth_child, 10)
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = result.values()
            assert len(values) == 2

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    def test_sync_client_update_relationships_where_raises_if_invalid_expression_provided(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            client.update(HasChild).where(2 == 2).set(HasChild.nth_child, 10).execute()


class TestSyncClientUpdateRelationshipsSet:
    def test_sync_client_update_relationships_set_with_descriptor(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(HasChild).set(HasChild.nth_child, 10).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    def test_sync_client_update_relationships_set_with_field_name(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(HasChild).set("nth_child", 10).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    def test_sync_client_update_relationships_set_with_expression_value(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(HasChild).set(HasChild.nth_child, HasChild.nth_child + 20).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] >= 20

    def test_sync_client_update_relationships_set_with_db_function(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = client.update(HasChild).set(HasChild.kind, to_upper(HasChild.kind)).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["kind"].startswith("BOY")

    def test_sync_client_update_relationships_set_overwrites_field_update_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with sync_driver.session() as session:
            result = session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            client.update(HasChild)
            .set(HasChild.nth_child, 10)
            .set(HasChild.nth_child, 40)
            .execute()
        )
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        with sync_driver.session() as session:
            result = session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 40

    def test_sync_client_update_relationships_set_raises_if_field_descriptor_is_for_wrong_model(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid field found. Expected a valid field of model {HasChild.__name__}, got name",
        ):
            client.update(HasChild).set(Adult.name, "name").execute()
