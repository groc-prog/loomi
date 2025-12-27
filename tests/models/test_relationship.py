# pylint: disable=missing-class-docstring, unused-variable

import pytest

from loomi.exceptions import ModelInitializationError
from loomi.models.relationship import LoomiRelationship


class TestModelHash:

    def test_relationship_hash_is_deterministic(self):
        """Verify that the hash generated for each model is deterministic."""

        class Likes(LoomiRelationship): ...

        hash_1 = Likes._generate_loomi_hash(set(Likes.loomi_config["type"]))  # type: ignore
        hash_2 = Likes._generate_loomi_hash(set(Likes.loomi_config["type"]))  # type: ignore
        assert hash_1 == hash_2


class TestConfiguration:
    def test_config_can_be_defined(self):
        """Verify that all configuration options can be defined via the class variable."""

        class Likes(LoomiRelationship):
            loomi_config = {
                "type": "LIKES_VERY_MUCH",
                "skip_constraints": True,
                "skip_indexes": False,
            }

        assert "type" in Likes.loomi_config
        assert Likes.loomi_config["type"] == "LIKES_VERY_MUCH"
        assert "skip_constraints" in Likes.loomi_config
        assert Likes.loomi_config["skip_constraints"]
        assert "skip_indexes" in Likes.loomi_config
        assert not Likes.loomi_config["skip_indexes"]

    def test_sets_type_if_not_defined(self):
        """Verify that type get set to the class name if not explicitly defined."""

        class Likes(LoomiRelationship): ...

        assert "type" in Likes.loomi_config
        assert Likes.loomi_config["type"] == "LIKES"

    def test_normalizes_multi_work_type_name(self):
        """Verify that the type for multi-name classes get normalized correctly."""

        class LikesVeryMuch(LoomiRelationship): ...

        assert "type" in LikesVeryMuch.loomi_config
        assert LikesVeryMuch.loomi_config["type"] == "LIKES_VERY_MUCH"


class TestInheritance:
    def test_inherits_config(self):
        """Verify that the configuration is inherited from other Loomi models."""

        class Likes(LoomiRelationship):
            loomi_config = {
                "type": "LIKES",
                "skip_constraints": True,
                "skip_indexes": False,
            }

        class Loves(Likes):
            loomi_config = {
                "type": "LOVES",
                "skip_constraints": False,
            }

        assert "type" in Loves.loomi_config
        assert Loves.loomi_config["type"] == "LOVES"
        assert "skip_constraints" in Loves.loomi_config
        assert not Loves.loomi_config["skip_constraints"]
        assert "skip_indexes" in Loves.loomi_config
        assert not Loves.loomi_config["skip_indexes"]

    def test_inherits_multiple_configs(self):
        """Verify that the configuration is inherited from multiple other Loomi models."""

        class Likes(LoomiRelationship):
            loomi_config = {
                "type": "LIKES",
                "skip_constraints": True,
                "skip_indexes": False,
            }

        class Loves(LoomiRelationship):
            loomi_config = {
                "skip_constraints": False,
            }

        class CanNotLiveWithout(Likes, Loves):
            loomi_config = {"skip_indexes": True}

        assert "type" in CanNotLiveWithout.loomi_config
        assert CanNotLiveWithout.loomi_config["type"] == "CAN_NOT_LIVE_WITHOUT"
        assert "skip_constraints" in CanNotLiveWithout.loomi_config
        assert CanNotLiveWithout.loomi_config["skip_constraints"]
        assert "skip_indexes" in CanNotLiveWithout.loomi_config
        assert CanNotLiveWithout.loomi_config["skip_indexes"]

    def test_inheritance_ignores_non_model_parents(self):
        """
        Verify that inheriting from classes which are not Loomi models does not affect the final
        config.
        """

        class Likes(LoomiRelationship):
            loomi_config = {
                "type": "LIKES",
                "skip_constraints": True,
                "skip_indexes": False,
            }

        class LikesUtils: ...

        class Loves(Likes, LikesUtils):
            loomi_config = {
                "type": "LOVES",
            }

        assert "type" in Loves.loomi_config
        assert Loves.loomi_config["type"] == "LOVES"
        assert "skip_constraints" in Loves.loomi_config
        assert Loves.loomi_config["skip_constraints"]
        assert "skip_indexes" in Loves.loomi_config
        assert not Loves.loomi_config["skip_indexes"]

    def test_raises_if_parent_does_not_expose_config(self):
        """Verify that a exception is raised if a parent class does not expose a configuration."""

        class Likes(LoomiRelationship): ...

        with pytest.raises(ModelInitializationError):
            Likes.loomi_config = None  # type: ignore

            class Loves(Likes):
                loomi_config = {
                    "type": "LOVES",
                    "skip_constraints": False,
                }
