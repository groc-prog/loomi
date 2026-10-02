# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi._async.session import AsyncSession
from loomi.exceptions import ClientError, SerializationError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from tests.conftest import DriverSpec


class Person(Node):
    name: str
    age: int
    active: bool = True

    loomi_config = {"labels": {"Person"}}


class Knows(Relationship):
    since: int = 2023

    loomi_config = {"type": "KNOWS"}


class TestAsyncClientInitialize:
    async def test_initialize_sets_server_type_and_version_for_configured_driver(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver)

        await client.initialize()

        assert client.server_type() == driver_spec.name
        assert client._server_version is not None
        assert len(client._server_version) > 0

    async def test_initialize_raises_client_error_when_driver_connectivity_fails(self):
        driver = SimpleNamespace()
        driver.verify_connectivity = AsyncMock(side_effect=RuntimeError("boom"))
        driver.get_server_info = AsyncMock()

        client = AsyncClient(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            await client.initialize()

    async def test_initialize_raises_client_error_when_version_query_returns_no_data(self):
        class MockResult:
            async def value(self):
                return []

        class MockSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_value, traceback):
                return None

            async def run(self, _query):
                return MockResult()

        driver = SimpleNamespace()
        driver.verify_connectivity = AsyncMock()
        driver.get_server_info = AsyncMock(return_value=SimpleNamespace(agent="Neo4j"))
        driver.session = lambda: MockSession()  # pylint: disable=unnecessary-lambda

        client = AsyncClient(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            await client.initialize()


class TestAsyncClientSession:
    async def test_session_returns_native_and_loomi_sessions_after_initialization(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()

        native_session = client.session(mode="native")
        loomi_session = client.session()

        assert isinstance(native_session, neo4j.AsyncSession)
        assert isinstance(loomi_session, AsyncSession)

    async def test_session_raises_client_error_before_client_is_initialized(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.session()


class TestAsyncClientRegistration:
    async def test_register_skips_invalid_model_and_continues_with_valid_models(
        self, async_driver: neo4j.AsyncDriver, caplog
    ):
        client = AsyncClient(async_driver)

        client.register(cast(Any, int), Person)

        assert "Invalid model" in caplog.text
        await client.initialize()
        client.register(Person)

        async with async_driver.session() as session:
            await session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = await client.query(Person).execute()
        assert len(results) == 1
        assert isinstance(results[0], Person)

    async def test_relationship_type_to_model_returns_none_when_not_strict(
        self, async_driver: neo4j.AsyncDriver, caplog
    ):
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()

        assert client._relationship_type_to_model("UNREGISTERED") is None
        assert "No model with type UNREGISTERED registered" in caplog.text

    async def test_relationship_type_to_model_raises_when_strict(
        self, async_driver: neo4j.AsyncDriver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()

        with pytest.raises(SerializationError, match="No model with type UNREGISTERED registered"):
            client._relationship_type_to_model("UNREGISTERED")
