# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import pathlib

import pytest
from neo4j import AsyncDriver, Driver

from loomi._async.client import AsyncClient
from loomi._sync.client import Client
from loomi.exceptions import ClientError, ModelError
from loomi.graph.node import Node
from tests.fixtures.db import DriverSpec, async_driver, driver_spec, sync_driver
from tests.internal.models.model_one import ModelOne
from tests.internal.models.nested.model_two import ModelTwo
from tests.internal.models.nested.non_model_two import NonModelTwo
from tests.internal.models.non_model_one import NonModelOne


class TestRegistration:
    @pytest.mark.integration
    def test_register_skips_non_model_classes(self, sync_driver: Driver, driver_spec: DriverSpec):
        """
        Verify that non model classes are skipped when passed to the `.register()` method.
        """

        class NotAModel: ...

        client = Client(sync_driver)
        client.register(NotAModel)  # type: ignore

        assert len(client._models) == 0

    @pytest.mark.integration
    def test_registers_classes_from_path(self, sync_driver: Driver, driver_spec: DriverSpec):
        """
        Verify that model classes are registered from a path.
        """
        models_dir = pathlib.Path(__file__).parent / "models"

        client = Client(sync_driver)
        client.register(models_dir)

        registered_models = client._models.values()

        assert len(client._models) == 2
        assert ModelTwo in registered_models
        assert ModelOne in registered_models
        assert NonModelOne not in registered_models
        assert NonModelTwo not in registered_models

    @pytest.mark.integration
    def test_raises_if_model_hash_is_not_initialized(
        self, sync_driver: Driver, driver_spec: DriverSpec
    ):
        """
        Verify that a exception if thrown if the models hash is not initialized when the model
        is registered.
        """

        class Human(Node): ...

        Human._hash = None
        client = Client(sync_driver)

        with pytest.raises(ModelError):
            client.register(Human)  # type: ignore


class TestInitialization:
    @pytest.mark.integration
    async def test_raises_if_not_initialized(
        self, sync_driver, async_driver: AsyncDriver, driver_spec: DriverSpec
    ):
        """
        Verify that a exception is thrown if a session is started without initializing the client.
        """
        sync_client = Client(sync_driver)

        with pytest.raises(ClientError):
            sync_client.session()

        with pytest.raises(ClientError):
            sync_client.session("native")

        async_client = AsyncClient(async_driver)

        with pytest.raises(ClientError):
            async_client.session()

        with pytest.raises(ClientError):
            async_client.session("native")
