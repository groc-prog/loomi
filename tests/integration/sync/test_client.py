# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._sync.client import Client
from loomi.exceptions import ClientError
from loomi.graph.node import Node


class TestSyncClientInitialization:
    def test_sync_client_raises_when_trying_to_interact_with_database_without_initializing(
        self, sync_driver
    ):
        class Human(Node): ...

        client = Client(sync_driver)

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.session()

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.query(Human).execute()

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.update(Human).execute()

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.delete(Human).execute()

    def test_sync_client_initialize_raises_if_server_not_reachable(self):
        driver = neo4j.GraphDatabase.driver("bolt://some.url")
        client = Client(driver)

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            client.initialize()

    def test_sync_client_initialize_verifies_connectivity_and_collects_server_info(
        self, sync_driver, driver_spec, mocker
    ):
        client = Client(sync_driver)

        connectivity_spy = mocker.spy(sync_driver, "verify_connectivity")
        server_info_spy = mocker.spy(sync_driver, "get_server_info")

        client.initialize()

        connectivity_spy.assert_called_once()
        server_info_spy.assert_called_once()
        assert client.server_type() == driver_spec.name
