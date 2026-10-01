# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi._async.transaction import AsyncTransaction
from loomi.graph.node import Node


class WrapperPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"WrapperPerson"}}


@pytest.fixture
async def async_wrapper_client(async_driver: neo4j.AsyncDriver):
    client = AsyncClient(async_driver)
    await client.initialize()
    client.register(WrapperPerson)
    return client


async def get_wrapper_person_tags(async_driver: neo4j.AsyncDriver) -> list[list[str]]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH (person:WrapperPerson) RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in await result.data()]


class TestAsyncTransaction:
    async def test_transaction_context_manager_commits_wrapped_query(
        self, async_driver: neo4j.AsyncDriver, async_wrapper_client
    ):
        async with async_wrapper_client.session() as session:
            transaction = await session.begin_transaction()
            async with transaction as entered_transaction:
                assert entered_transaction is transaction
                result = await transaction.run(
                    "CREATE (person:WrapperPerson {name: $name, tags: $tags}) " + "RETURN person",
                    name="Alice",
                    tags=["committed"],
                )
                record = await result.single()
                assert record is not None
                assert isinstance(record["person"], WrapperPerson)

        assert await get_wrapper_person_tags(async_driver) == [["committed"]]

    async def test_transaction_context_manager_rolls_back_when_body_fails(
        self, async_driver: neo4j.AsyncDriver, async_wrapper_client
    ):
        async with async_wrapper_client.session() as session:
            with pytest.raises(RuntimeError, match="abort transaction"):
                async with await session.begin_transaction() as transaction:
                    await transaction.run(
                        "CREATE (:WrapperPerson {name: $name, tags: $tags})",
                        name="Alice",
                        tags=["rolled-back"],
                    )
                    raise RuntimeError("abort transaction")

        assert await get_wrapper_person_tags(async_driver) == []

    async def test_transaction_run_tracking_flushes_changes_in_same_transaction(
        self, async_driver: neo4j.AsyncDriver, async_wrapper_client
    ):
        async with async_driver.session() as native_session:
            await native_session.run("CREATE (:WrapperPerson {name: 'Alice', tags: ['before']})")

        async with async_wrapper_client.session() as session:
            async with await session.begin_transaction() as transaction:
                result = await transaction.run(
                    "MATCH (person:WrapperPerson) RETURN person", tracking=True
                )
                record = await result.single()
                assert record is not None
                assert isinstance(record["person"], WrapperPerson)
                record["person"].tags = ["after"]
                await transaction.change_tracker.flush()

        assert await get_wrapper_person_tags(async_driver) == [["after"]]

    async def test_transaction_change_tracker_is_available(self, async_wrapper_client):
        async with async_wrapper_client.session() as session:
            transaction = await session.begin_transaction()
            assert transaction.change_tracker is not None
            await transaction.rollback()

    async def test_transaction_delegates_unknown_attributes_to_native_transaction(self):
        native_transaction = SimpleNamespace(delegated_value="native-transaction-value")
        transaction = AsyncTransaction(cast(Any, native_transaction), cast(Any, None))

        assert transaction.delegated_value == "native-transaction-value"

    async def test_transaction_run_propagates_native_driver_error(self):
        native_transaction = SimpleNamespace(
            run=AsyncMock(side_effect=RuntimeError("transaction failed"))
        )
        transaction = AsyncTransaction(cast(Any, native_transaction), cast(Any, None))

        with pytest.raises(RuntimeError, match="transaction failed"):
            await transaction.run("RETURN 1")
