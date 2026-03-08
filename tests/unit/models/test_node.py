# pylint: disable=missing-class-docstring, unused-variable, unused-argument

import pytest

from loomi.exceptions import ModelError
from loomi.models.node import Node


class TestModelHash:
    def test_node_hash_is_deterministic(self):
        """Verify that the hash generated for each model is deterministic."""

        class Human(Node): ...

        hash_1 = Human._generate_hash(Human.loomi_config["labels"])  # type: ignore
        hash_2 = Human._generate_hash(Human.loomi_config["labels"])  # type: ignore
        assert hash_1 == hash_2


class TestRepr:
    def test_repr_contains_model_info(self):
        """Verify that the repr contains similar info about the model to the neo4j package"""

        class Worker(Node):
            loomi_config = {"labels": {"Worker"}}

        repr_ = repr(Worker())
        assert repr_ == "<Worker element_id=None labels={'Worker'}>"

        worker = Worker()
        worker._element_id = "element_id"

        repr_ = repr(worker)
        assert repr_ == "<Worker element_id='element_id' labels={'Worker'}>"


class TestConfiguration:
    def test_config_can_be_defined(self):
        """Verify that all configuration options can be defined via the class variable."""

        class Human(Node):
            loomi_config = {"labels": {"Humanoid"}}

        assert "labels" in Human.loomi_config
        assert Human.loomi_config["labels"] == {"Humanoid"}

    def test_sets_labels_if_not_defined(self):
        """Verify that labels get set to the class name if not explicitly defined."""

        class Human(Node): ...

        assert "labels" in Human.loomi_config
        assert Human.loomi_config["labels"] == {"Human"}


class TestInheritance:
    def test_inherits_config(self):
        """Verify that the configuration is inherited from other  models."""

        def serialize_1(*args, **kwargs): ...
        def serialize_2(*args, **kwargs): ...

        def deserialize_1(*args, **kwargs): ...
        def deserialize_2(*args, **kwargs): ...

        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
                "deserializer_fn": deserialize_1,
                "serializer_fn": serialize_1,
            }

        class Worker(Human):
            loomi_config = {
                "labels": {"Worker"},
            }

        class Farmer(Human):
            loomi_config = {
                "labels": {"Farmer"},
                "deserializer_fn": deserialize_2,
                "serializer_fn": serialize_2,
            }

        assert "labels" in Worker.loomi_config
        assert Worker.loomi_config["labels"] == {"Human", "Worker"}

        assert "serializer_fn" in Worker.loomi_config
        assert Worker.loomi_config["serializer_fn"] is serialize_1

        assert "deserializer_fn" in Worker.loomi_config
        assert Worker.loomi_config["deserializer_fn"] is deserialize_1

        assert "labels" in Farmer.loomi_config
        assert Farmer.loomi_config["labels"] == {"Human", "Farmer"}

        assert "serializer_fn" in Farmer.loomi_config
        assert Farmer.loomi_config["serializer_fn"] is serialize_2

        assert "deserializer_fn" in Farmer.loomi_config
        assert Farmer.loomi_config["deserializer_fn"] is deserialize_2

    def test_inherits_multiple_configs(self):
        """Verify that the configuration is inherited from multiple other  models."""

        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
            }

        class Worker(Node):
            loomi_config = {
                "labels": {"Worker"},
            }

        class Person(Human, Worker):
            loomi_config = {
                "labels": {"Person"},
            }

        assert "labels" in Person.loomi_config
        assert Person.loomi_config["labels"] == {"Human", "Worker", "Person"}

    def test_inheritance_ignores_non_model_parents(self):
        """
        Verify that inheriting from classes which are not  models does not affect the final
        config.
        """

        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
            }

        class HumanUtils: ...

        class Person(Human, HumanUtils):
            loomi_config = {
                "labels": {"Person"},
            }

        assert "labels" in Person.loomi_config
        assert Person.loomi_config["labels"] == {"Human", "Person"}

    def test_raises_if_parent_does_not_expose_config(self):
        """Verify that a exception is raised if a parent class does not expose a configuration."""

        class Human(Node): ...

        with pytest.raises(ModelError):
            Human.loomi_config = None  # type: ignore

            class Worker(Human):
                loomi_config = {
                    "labels": {"Worker"},
                }
