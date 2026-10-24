# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi.exceptions import ModelError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


@pytest.fixture
def mocked_async_driver():
    driver = neo4j.AsyncGraphDatabase.driver("bolt://some.url")

    yield driver


class TestAsyncClientModelRegistration:
    def test_async_client_model_registration_raises_if_model_hash_not_available(
        self, mocked_async_driver
    ):
        class Human(Node): ...

        client = AsyncClient(mocked_async_driver)
        Human._hash = None

        with pytest.raises(
            ModelError,
            match=f"Hash on model {Human.__name__} is not initialized. Maybe you forgot to call {Human.model_rebuild.__name__}?",
        ):
            client.register(Human)

    def test_async_client_model_registration_skips_non_node_and_relationship_classes(
        self, mocked_async_driver
    ):
        class Human(Node): ...

        class Likes(Relationship): ...

        class NotAModel: ...

        client = AsyncClient(mocked_async_driver)
        client.register(Human, Likes, NotAModel)  # type: ignore

        assert len(client._models) == 2
        assert Human._hash in client._models
        assert Likes._hash in client._models

    def test_async_client_model_registration_overwrites_models_with_identical_hash(
        self, mocked_async_driver
    ):
        class Human1(Node):
            loomi_config = {"labels": {"Human"}}

        class Likes1(Relationship):
            loomi_config = {"type": "LIKES"}

        class Human2(Node):
            loomi_config = {"labels": {"Human"}}

        class Likes2(Relationship):
            loomi_config = {"type": "LIKES"}

        client = AsyncClient(mocked_async_driver)
        client.register(Human1, Human2, Likes1, Likes2)

        assert len(client._models) == 2
        assert Human2._hash in client._models
        assert Likes2._hash in client._models
