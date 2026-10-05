# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from loomi._async.client import AsyncClient
from loomi._async.session import AsyncSession
from loomi._async.transaction import AsyncTransaction
from loomi.graph.node import Node


class WrapperPerson(Node):
    name: str
    tags: list[str]

    loomi_config = {"labels": {"WrapperPerson"}}


@pytest.fixture
async def async_wrapper_client(async_driver):
    client = AsyncClient(async_driver)
    await client.initialize()
    client.register(WrapperPerson)
    return client


async def get_wrapper_person_tags(async_driver) -> list[list[str]]:
    async with async_driver.session() as session:
        result = await session.run(
            "MATCH (person:WrapperPerson) RETURN person.tags AS tags ORDER BY person.tags[0]"
        )
        return [record["tags"] for record in await result.data()]


class TestAsyncSession:
    async def test_session_context_manager_runs_and_transforms_database_results(
        self, async_driver, async_wrapper_client
    ):
        async with async_wrapper_client.session() as session:
            assert isinstance(session, AsyncSession)
            result = await session.run("RETURN $answer AS answer", {"answer": 42})
            record = await result.single()

        assert record is not None
        assert record["answer"] == 42

    async def test_session_run_tracking_persists_transformed_node_on_flush(
        self, async_driver, async_wrapper_client
    ):
        async with async_driver.session() as native_session:
            await native_session.run("CREATE (:WrapperPerson {name: 'Alice', tags: ['before']})")

        async with async_wrapper_client.session() as session:
            result = await session.run("MATCH (person:WrapperPerson) RETURN person", tracking=True)
            record = await result.single()
            assert record is not None
            assert isinstance(record["person"], WrapperPerson)
            record["person"].tags = ["after"]
            await session.change_tracker.flush()

        assert await get_wrapper_person_tags(async_driver) == [["after"]]

    async def test_session_begin_transaction_returns_wrapper_and_commits_on_context_exit(
        self, async_driver, async_wrapper_client
    ):
        async with async_wrapper_client.session() as session:
            async with await session.begin_transaction(metadata={"source": "test"}) as tx:
                assert isinstance(tx, AsyncTransaction)
                result = await tx.run(
                    "CREATE (person:WrapperPerson {name: $name, tags: $tags}) " + "RETURN person",
                    {"name": "Alice", "tags": ["transaction"]},
                )
                record = await result.single()
                assert record is not None
                assert isinstance(record["person"], WrapperPerson)

        assert await get_wrapper_person_tags(async_driver) == [["transaction"]]

    async def test_session_begin_transaction_forwards_timeout(
        self, async_driver, async_wrapper_client
    ):
        async with async_wrapper_client.session() as session:
            transaction = await session.begin_transaction(timeout=30.0)
            assert isinstance(transaction, AsyncTransaction)
            await transaction.rollback()

    async def test_session_delegates_unknown_attributes_to_native_session(self):
        native_session = SimpleNamespace(delegated_value="native-session-value")
        session = AsyncSession(cast(Any, native_session), cast(Any, None))

        assert session.delegated_value == "native-session-value"

    async def test_session_run_propagates_native_driver_error(self):
        native_session = SimpleNamespace(run=AsyncMock(side_effect=RuntimeError("session failed")))
        session = AsyncSession(cast(Any, native_session), cast(Any, None))

        with pytest.raises(RuntimeError, match="session failed"):
            await session.run("RETURN 1")
