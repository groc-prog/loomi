# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import neo4j
import pytest

from loomi._sync.client import Client
from loomi._sync.result import Result
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class ResultPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"SyncResultPerson"}}


class ResultKnows(Relationship):
    history: list[int]

    loomi_config = {"type": "SYNC_RESULT_KNOWS"}


@pytest.fixture
def sync_result_client(sync_driver: neo4j.Driver):
    client = Client(sync_driver)
    client.initialize()
    client.register(ResultPerson, ResultKnows)
    return client


@pytest.fixture
def sync_result_session(sync_result_client):
    with sync_result_client.session() as session:
        yield session


def create_result_people(sync_driver: neo4j.Driver) -> None:
    with sync_driver.session() as session:
        session.run(
            """
            CREATE (:SyncResultPerson {name: 'Alice', tags: ['alice']})
            CREATE (:SyncResultPerson {name: 'Bob', tags: ['bob']})
            """
        )


def create_result_graph(sync_driver: neo4j.Driver) -> None:
    with sync_driver.session() as session:
        session.run(
            """
            CREATE (alice:SyncResultPerson {name: 'Alice', tags: ['alice']})
            CREATE (bob:SyncResultPerson {name: 'Bob', tags: ['bob']})
            CREATE (alice)-[:SYNC_RESULT_KNOWS {history: [2024]}]->(bob)
            """
        )


def get_result_person_tags(sync_driver: neo4j.Driver) -> list[list[str]]:
    with sync_driver.session() as session:
        result = session.run(
            "MATCH (person:SyncResultPerson) "
            + "RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in result.data()]


def get_result_relationship_history(sync_driver: neo4j.Driver) -> list[list[int]]:
    with sync_driver.session() as session:
        result = session.run(
            "MATCH ()-[relationship:SYNC_RESULT_KNOWS]->() "
            "RETURN relationship.history AS history"
        )
        return [record["history"] for record in result.data()]


class TestSyncResultIteration:
    def test_sync_iteration_transforms_node_records(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) RETURN person ORDER BY person.name"
        )
        records = [record for record in result]

        assert [record["person"].name for record in records] == ["Alice", "Bob"]
        assert all(isinstance(record["person"], ResultPerson) for record in records)

    def test_anext_transforms_next_node_record(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) RETURN person ORDER BY person.name"
        )
        record = result.__next__()

        assert isinstance(record["person"], ResultPerson)
        assert record["person"].name == "Alice"

    def test_sync_iteration_tracking_persists_mutated_node_on_flush(
        self, sync_driver, sync_result_session
    ):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        for record in result:
            record["person"].tags = ["iterated"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["iterated"]]

    def test_anext_tracking_persists_mutated_node_on_flush(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        record = result.__next__()
        record["person"].tags = ["anext"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["anext"], ["bob"]]


class TestSyncResultPeek:
    def test_peek_transforms_record_without_consuming_it(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person"
        )
        peeked = result.peek()
        next_record = result.single()

        assert isinstance(peeked["person"], ResultPerson)
        assert isinstance(next_record["person"], ResultPerson)
        assert peeked["person"].name == next_record["person"].name == "Alice"

    def test_peek_returns_none_for_empty_result(self, sync_result_session):
        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'missing' RETURN person"
        )

        assert result.peek() is None

    def test_peek_tracking_persists_mutated_node_on_flush(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        record = result.peek()
        record["person"].tags = ["peeked"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["peeked"]]


class TestSyncResultFetch:
    def test_fetch_transforms_each_node_record(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) RETURN person ORDER BY person.name"
        )
        records = result.fetch(2)

        assert [record["person"].name for record in records] == ["Alice", "Bob"]
        assert all(isinstance(record["person"], ResultPerson) for record in records)

    def test_fetch_tracking_persists_mutated_node_on_flush(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        records = result.fetch(1)
        records[0]["person"].tags = ["fetched"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["fetched"]]

    def test_fetch_propagates_underlying_driver_error(self):
        underlying = SimpleNamespace(fetch=Mock(side_effect=RuntimeError("fetch failed")))
        result = Result(underlying, cast(Any, None), None)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError, match="fetch failed"):
            result.fetch(1)


class TestSyncResultEager:
    def test_to_eager_result_transforms_records(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) RETURN person ORDER BY person.name"
        )
        eager = result.to_eager_result()

        assert isinstance(eager, neo4j.EagerResult)
        assert [record["person"].name for record in eager.records] == ["Alice", "Bob"]
        assert all(isinstance(record["person"], ResultPerson) for record in eager.records)

    def test_to_eager_result_tracking_persists_mutated_node_on_flush(
        self, sync_driver, sync_result_session
    ):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        eager = result.to_eager_result()
        eager.records[0]["person"].tags = ["eager"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["eager"]]


class TestSyncResultSingle:
    def test_single_transforms_returned_relationship_record(self, sync_driver, sync_result_session):
        create_result_graph(sync_driver)

        result = sync_result_session.run(
            "MATCH ()-[relationship:SYNC_RESULT_KNOWS]->() RETURN relationship"
        )
        record = result.single()

        assert record is not None
        assert isinstance(record["relationship"], ResultKnows)
        assert record["relationship"].history == [2024]

    def test_single_returns_none_when_no_record_exists(self, sync_result_session):
        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'missing' RETURN person"
        )

        assert result.single() is None

    def test_single_strict_propagates_driver_error_for_empty_result(self):
        underlying = SimpleNamespace(
            single=Mock(side_effect=neo4j.exceptions.ResultNotSingleError("no record"))
        )
        result = Result(underlying, cast(Any, None), None)  # type: ignore[arg-type]

        with pytest.raises(neo4j.exceptions.ResultNotSingleError):
            result.single(strict=True)

    def test_single_tracking_persists_mutated_node_on_flush(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        record = result.single()
        record["person"].tags = ["single"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["single"]]


class TestSyncResultValues:
    def test_values_transforms_requested_entity_column(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) RETURN person ORDER BY person.name"
        )
        values = result.values("person")

        assert [row[0].name for row in values] == ["Alice", "Bob"]
        assert all(isinstance(row[0], ResultPerson) for row in values)

    def test_values_tracking_persists_mutated_node_on_flush(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        values = result.values("person")
        values[0][0].tags = ["values"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["values"]]


class TestSyncResultValue:
    def test_value_transforms_entity_list(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) RETURN person ORDER BY person.name"
        )
        values = result.value()

        assert [person.name for person in values] == ["Alice", "Bob"]
        assert all(isinstance(person, ResultPerson) for person in values)

    def test_value_preserves_default_for_empty_values(self, sync_result_session):
        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'missing' RETURN person"
        )

        assert result.value(default="empty") == []

    def test_value_tracking_persists_mutated_node_on_flush(self, sync_driver, sync_result_session):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person",
            tracking=True,
        )
        values = result.value()
        values[0].tags = ["value"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["bob"], ["value"]]


class TestSyncResultGraph:
    def test_graph_transforms_nodes_relationship_and_type(self, sync_driver, sync_result_session):
        create_result_graph(sync_driver)

        result = sync_result_session.run(
            "MATCH (start:SyncResultPerson)-[relationship:SYNC_RESULT_KNOWS]->(end) "
            "RETURN start, relationship, end"
        )
        graph = result.graph()

        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert all(isinstance(node, ResultPerson) for node in graph.nodes)
        assert all(isinstance(relationship, ResultKnows) for relationship in graph.relationships)
        assert graph.relationship_type("SYNC_RESULT_KNOWS") is ResultKnows

    def test_graph_tracking_persists_mutated_nodes_and_relationship(
        self, sync_driver, sync_result_session
    ):
        create_result_graph(sync_driver)

        result = sync_result_session.run(
            "MATCH (start:SyncResultPerson)-[relationship:SYNC_RESULT_KNOWS]->(end) "
            "RETURN start, relationship, end",
            tracking=True,
        )
        graph = result.graph()
        for node in graph.nodes:
            node.tags = ["graph"]
        for relationship in graph.relationships:
            relationship.history = [2025]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["graph"], ["graph"]]
        assert get_result_relationship_history(sync_driver) == [[2025]]


class TestSyncResultTracking:
    def test_disabled_tracking_does_not_persist_mutated_result_entity(
        self, sync_driver, sync_result_session
    ):
        create_result_people(sync_driver)

        result = sync_result_session.run(
            "MATCH (person:SyncResultPerson) WHERE person.name = 'Alice' RETURN person"
        )
        record = result.single()
        record["person"].tags = ["not-tracked"]
        sync_result_session.change_tracker.flush()

        assert get_result_person_tags(sync_driver) == [["alice"], ["bob"]]

    def test_tracking_ignores_primitive_result_values(self, sync_result_session):
        result = sync_result_session.run("RETURN 42 AS answer", tracking=True)

        record = result.single()
        assert record["answer"] == 42

        sync_result_session.change_tracker.flush()


class TestSyncResultDelegation:
    def test_unknown_attributes_are_delegated_to_native_result(self, sync_result_session):
        result = sync_result_session.run("RETURN 1 AS answer")

        assert result.keys() == ["answer"]
