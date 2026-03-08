# pylint: disable=missing-class-docstring, unused-variable, unused-argument

import pytest

from loomi.exceptions import ModelError
from loomi.models.relationship import Relationship


class TestModelHash:

    def test_relationship_hash_is_deterministic(self):
        """Verify that the hash generated for each model is deterministic."""

        class Likes(Relationship): ...

        hash_1 = Likes._generate_hash(set(Likes.loomi_config["type"]))  # type: ignore
        hash_2 = Likes._generate_hash(set(Likes.loomi_config["type"]))  # type: ignore
        assert hash_1 == hash_2


class TestRepr:
    def test_repr_contains_model_info(self):
        """Verify that the repr contains similar info about the model to the neo4j package"""

        class Likes(Relationship):
            loomi_config = {"type": "LIKES"}

        repr_ = repr(Likes())
        assert repr_ == "<Likes element_id=None type='LIKES'>"

        likes = Likes()
        likes._element_id = "element_id"

        repr_ = repr(likes)
        assert repr_ == "<Likes element_id='element_id' type='LIKES'>"


class TestConfiguration:
    def test_config_can_be_defined(self):
        """Verify that all configuration options can be defined via the class variable."""

        class Likes(Relationship):
            loomi_config = {
                "type": "LIKES_VERY_MUCH",
            }

        assert "type" in Likes.loomi_config
        assert Likes.loomi_config["type"] == "LIKES_VERY_MUCH"

    def test_sets_type_if_not_defined(self):
        """Verify that type get set to the class name if not explicitly defined."""

        class Likes(Relationship): ...

        assert "type" in Likes.loomi_config
        assert Likes.loomi_config["type"] == "LIKES"

    def test_normalizes_multi_work_type_name(self):
        """Verify that the type for multi-name classes get normalized correctly."""

        class LikesVeryMuch(Relationship): ...

        assert "type" in LikesVeryMuch.loomi_config
        assert LikesVeryMuch.loomi_config["type"] == "LIKES_VERY_MUCH"


class TestInheritance:
    def test_inherits_config(self):
        """Verify that the configuration is inherited from other  models."""

        def serialize_1(*args, **kwargs): ...
        def serialize_2(*args, **kwargs): ...

        def deserialize_1(*args, **kwargs): ...
        def deserialize_2(*args, **kwargs): ...

        class Likes(Relationship):
            loomi_config = {
                "type": "LIKES",
                "deserializer_fn": deserialize_1,
                "serializer_fn": serialize_1,
            }

        class Loves(Likes):
            loomi_config = {"type": "LOVES"}

        class Hates(Likes):
            loomi_config = {
                "type": "HATES",
                "deserializer_fn": deserialize_2,
                "serializer_fn": serialize_2,
            }

        assert "type" in Loves.loomi_config
        assert Loves.loomi_config["type"] == "LOVES"

        assert "serializer_fn" in Loves.loomi_config
        assert Loves.loomi_config["serializer_fn"] is serialize_1

        assert "deserializer_fn" in Loves.loomi_config
        assert Loves.loomi_config["deserializer_fn"] is deserialize_1

        assert "type" in Hates.loomi_config
        assert Hates.loomi_config["type"] == "HATES"

        assert "serializer_fn" in Hates.loomi_config
        assert Hates.loomi_config["serializer_fn"] is serialize_2

        assert "deserializer_fn" in Hates.loomi_config
        assert Hates.loomi_config["deserializer_fn"] is deserialize_2

    def test_raises_if_parent_does_not_expose_config(self):
        """Verify that a exception is raised if a parent class does not expose a configuration."""

        class Likes(Relationship): ...

        with pytest.raises(ModelError):
            Likes.loomi_config = None  # type: ignore

            class Loves(Likes):
                loomi_config = {"type": "LOVES"}
