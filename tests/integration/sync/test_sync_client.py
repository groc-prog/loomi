# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import neo4j
import pytest

from loomi._sync.client import Client
from loomi._sync.session import Session
from loomi.exceptions import ClientError, QueryError, SerializationError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api.constants import OrderBy
from tests.conftest import DriverSpec


class Person(Node):
    name: str
    age: int
    active: bool = True

    loomi_config = {"labels": {"Person"}}


class Knows(Relationship):
    since: int = 2023

    loomi_config = {"type": "KNOWS"}


class TestSyncClientInitialize:
    def test_initialize_sets_server_type_and_version_for_configured_driver(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver)

        client.initialize()

        assert client.server_type() == driver_spec.name
        assert client._server_version is not None
        assert len(client._server_version) > 0

    def test_initialize_raises_client_error_when_driver_connectivity_fails(self):
        driver = SimpleNamespace()
        driver.verify_connectivity = Mock(side_effect=RuntimeError("boom"))
        driver.get_server_info = Mock()

        client = Client(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            client.initialize()

    def test_initialize_raises_client_error_when_version_query_returns_no_data(self):
        class MockResult:
            def value(self):
                return []

        class MockSession:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def run(self, _query):
                return MockResult()

        driver = SimpleNamespace()
        driver.verify_connectivity = Mock()
        driver.get_server_info = Mock(return_value=SimpleNamespace(agent="Neo4j"))
        driver.session = lambda: MockSession()  # pylint: disable=unnecessary-lambda

        client = Client(driver)  # type: ignore[arg-type]

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            client.initialize()


class TestSyncClientSession:
    def test_session_returns_native_and_loomi_sessions_after_initialization(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()

        native_session = client.session(mode="native")
        loomi_session = client.session()

        assert isinstance(native_session, neo4j.Session)
        assert isinstance(loomi_session, Session)

    def test_session_raises_client_error_before_client_is_initialized(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.session()


class TestSyncClientRegistration:
    def test_register_skips_invalid_model_and_continues_with_valid_models(
        self, sync_driver: neo4j.Driver, caplog
    ):
        client = Client(sync_driver)

        client.register(cast(Any, int), Person)

        assert "Invalid model" in caplog.text
        client.initialize()
        client.register(Person)

        with sync_driver.session() as session:
            session.run("CREATE (:Person {name: 'Alice', age: 30, active: true})")

        results = client.query(Person).execute()
        assert len(results) == 1
        assert isinstance(results[0], Person)

    def test_relationship_type_to_model_returns_none_when_not_strict(
        self, sync_driver: neo4j.Driver, caplog
    ):
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()

        assert client._relationship_type_to_model("UNREGISTERED") is None
        assert "No model with type UNREGISTERED registered" in caplog.text

    def test_relationship_type_to_model_raises_when_strict(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()

        with pytest.raises(SerializationError, match="No model with type UNREGISTERED registered"):
            client._relationship_type_to_model("UNREGISTERED")
