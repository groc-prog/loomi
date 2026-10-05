# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest

from loomi._sync.client import Client
from loomi._sync.session import Session
from loomi._sync.transaction import Transaction
from loomi.graph.node import Node


class WrapperPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"WrapperPerson"}}


@pytest.fixture
def sync_wrapper_client(sync_driver):
    client = Client(sync_driver)
    client.initialize()
    client.register(WrapperPerson)
    return client


def get_wrapper_person_tags(sync_driver) -> list[list[str]]:
    with sync_driver.session() as session:
        result = session.run(
            "MATCH (person:WrapperPerson) RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in result.data()]


class TestSyncSession:
    def test_session_context_manager_runs_and_transforms_database_results(
        self, sync_driver, sync_wrapper_client
    ):
        with sync_wrapper_client.session() as session:
            assert isinstance(session, Session)
            result = session.run("RETURN $answer AS answer", {"answer": 42})
            record = result.single()

        assert record is not None
        assert record["answer"] == 42

    def test_session_run_tracking_persists_transformed_node_on_flush(
        self, sync_driver, sync_wrapper_client
    ):
        with sync_driver.session() as native_session:
            native_session.run("CREATE (:WrapperPerson {name: 'Alice', tags: ['before']})")

        with sync_wrapper_client.session() as session:
            result = session.run("MATCH (person:WrapperPerson) RETURN person", tracking=True)
            record = result.single()
            assert record is not None
            assert isinstance(record["person"], WrapperPerson)
            record["person"].tags = ["after"]
            session.change_tracker.flush()

        assert get_wrapper_person_tags(sync_driver) == [["after"]]

    def test_session_begin_transaction_returns_wrapper_and_commits_on_context_exit(
        self, sync_driver, sync_wrapper_client
    ):
        with sync_wrapper_client.session() as session:
            with session.begin_transaction(metadata={"source": "test"}) as tx:
                assert isinstance(tx, Transaction)
                result = tx.run(
                    "CREATE (person:WrapperPerson {name: $name, tags: $tags}) " + "RETURN person",
                    {"name": "Alice", "tags": ["transaction"]},
                )
                record = result.single()
                assert record is not None
                assert isinstance(record["person"], WrapperPerson)

        assert get_wrapper_person_tags(sync_driver) == [["transaction"]]

    def test_session_begin_transaction_forwards_timeout(self, sync_driver, sync_wrapper_client):
        with sync_wrapper_client.session() as session:
            transaction = session.begin_transaction(timeout=30.0)
            assert isinstance(transaction, Transaction)
            transaction.rollback()

    def test_session_delegates_unknown_attributes_to_native_session(self):
        native_session = SimpleNamespace(delegated_value="native-session-value")
        session = Session(cast(Any, native_session), cast(Any, None))

        assert session.delegated_value == "native-session-value"

    def test_session_run_propagates_native_driver_error(self):
        native_session = SimpleNamespace(run=Mock(side_effect=RuntimeError("session failed")))
        session = Session(cast(Any, native_session), cast(Any, None))

        with pytest.raises(RuntimeError, match="session failed"):
            session.run("RETURN 1")
