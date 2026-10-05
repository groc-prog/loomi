# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest

from loomi._sync.client import Client
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


class TestSyncTransaction:
    def test_transaction_context_manager_commits_wrapped_query(
        self, sync_driver, sync_wrapper_client
    ):
        with sync_wrapper_client.session() as session:
            transaction = session.begin_transaction()
            with transaction as entered_transaction:
                assert entered_transaction is transaction
                result = transaction.run(
                    "CREATE (person:WrapperPerson {name: $name, tags: $tags}) " + "RETURN person",
                    name="Alice",
                    tags=["committed"],
                )
                record = result.single()
                assert record is not None
                assert isinstance(record["person"], WrapperPerson)

        assert get_wrapper_person_tags(sync_driver) == [["committed"]]

    def test_transaction_context_manager_rolls_back_when_body_fails(
        self, sync_driver, sync_wrapper_client
    ):
        with sync_wrapper_client.session() as session:
            with pytest.raises(RuntimeError, match="abort transaction"):
                with session.begin_transaction() as transaction:
                    transaction.run(
                        "CREATE (:WrapperPerson {name: $name, tags: $tags})",
                        name="Alice",
                        tags=["rolled-back"],
                    )
                    raise RuntimeError("abort transaction")

        assert get_wrapper_person_tags(sync_driver) == []

    def test_transaction_run_tracking_flushes_changes_in_same_transaction(
        self, sync_driver, sync_wrapper_client
    ):
        with sync_driver.session() as native_session:
            native_session.run("CREATE (:WrapperPerson {name: 'Alice', tags: ['before']})")

        with sync_wrapper_client.session() as session:
            with session.begin_transaction() as transaction:
                result = transaction.run(
                    "MATCH (person:WrapperPerson) RETURN person", tracking=True
                )
                record = result.single()
                assert record is not None
                assert isinstance(record["person"], WrapperPerson)
                record["person"].tags = ["after"]
                transaction.change_tracker.flush()

        assert get_wrapper_person_tags(sync_driver) == [["after"]]

    def test_transaction_change_tracker_is_available(self, sync_wrapper_client):
        with sync_wrapper_client.session() as session:
            transaction = session.begin_transaction()
            assert transaction.change_tracker is not None
            transaction.rollback()

    def test_transaction_delegates_unknown_attributes_to_native_transaction(self):
        native_transaction = SimpleNamespace(delegated_value="native-transaction-value")
        transaction = Transaction(cast(Any, native_transaction), cast(Any, None))

        assert transaction.delegated_value == "native-transaction-value"

    def test_transaction_run_propagates_native_driver_error(self):
        native_transaction = SimpleNamespace(
            run=Mock(side_effect=RuntimeError("transaction failed"))
        )
        transaction = Transaction(cast(Any, native_transaction), cast(Any, None))

        with pytest.raises(RuntimeError, match="transaction failed"):
            transaction.run("RETURN 1")
