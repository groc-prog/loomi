# pylint: disable=missing-class-docstring, redefined-outer-name, unused-import, unused-argument

import pytest
from neo4j import AsyncDriver, Driver

from loomi.client.async_client import LoomiAsyncClient
from loomi.client.sync_client import LoomiClient
from loomi.exceptions import ClientError, ModelError
from loomi.models.node import LoomiNode
from tests.fixtures.db import DriverSpec, async_driver, driver_spec, sync_driver


class TestRegistration:

    def test_register_skips_non_model_classes(self, sync_driver: Driver, driver_spec: DriverSpec):
        """
        Verify that non model classes are skipped when passed to the `.register()` method.
        """

        class NotAModel: ...

        client = LoomiClient(sync_driver)
        client.register(NotAModel)  # type: ignore

        assert len(client._models) == 0

    def test_raises_if_model_hash_is_not_initialized(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that a exception if thrown if the models hash is not initialized when the model
        is registered.
        """

        class Human(LoomiNode): ...

        Human._hash = None
        client = LoomiClient(sync_driver)

        with pytest.raises(ModelError):
            client.register(Human)  # type: ignore


class TestInitialization:
    async def test_raises_if_not_initialized(
        self, sync_driver, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that a exception is thrown if a session is started without initializing the client.
        """
        sync_client = LoomiClient(sync_driver)

        with pytest.raises(ClientError):
            sync_client.session()

        with pytest.raises(ClientError):
            sync_client.session("native")

        async_client = LoomiAsyncClient(async_driver)

        with pytest.raises(ClientError):
            async_client.session()

        with pytest.raises(ClientError):
            async_client.session("native")
