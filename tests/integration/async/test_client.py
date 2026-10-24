# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi.exceptions import ClientError
from loomi.graph.node import Node


class TestSyncClientInitialization:
    async def test_async_client_raises_when_trying_to_interact_with_database_without_initializing(
        self, async_driver
    ):
        class Human(Node): ...

        client = AsyncClient(async_driver)

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            client.session()

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            await client.query(Human).execute()

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            await client.update(Human).execute()

        with pytest.raises(
            ClientError, match="Client must be initialized before method can be called"
        ):
            await client.delete(Human).execute()

    async def test_async_client_initialize_raises_if_server_not_reachable(self):
        driver = neo4j.AsyncGraphDatabase.driver("bolt://some.url")
        client = AsyncClient(driver)

        with pytest.raises(ClientError, match="Could not get required metadata from remote"):
            await client.initialize()

    async def test_async_client_initialize_verifies_connectivity_and_collects_server_info(
        self, async_driver, driver_spec, mocker
    ):
        client = AsyncClient(async_driver)

        connectivity_spy = mocker.spy(async_driver, "verify_connectivity")
        server_info_spy = mocker.spy(async_driver, "get_server_info")

        await client.initialize()

        connectivity_spy.assert_called_once()
        server_info_spy.assert_called_once()
        assert client.server_type() == driver_spec.name
