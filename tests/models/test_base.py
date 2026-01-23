# pylint: disable=missing-class-docstring

from typing import Optional

from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship


class TestModelHash:

    def test_hash_with_same_inputs_has_different_result_with_different_entity(self):
        """
        Verify that same inputs for node and relationship model hashes result in different
        strings.
        """

        class Human(LoomiNode): ...

        class Likes(LoomiRelationship): ...

        hash_1 = Human._generate_loomi_hash(set("input"))  # type: ignore
        hash_2 = Likes._generate_loomi_hash(set("input"))  # type: ignore
        assert hash_1 != hash_2


class TestFieldDefaults:
    def test_model_default_values(self):
        """Verify that a model is initialized with the correct defaults for graph related fields."""

        class Human(LoomiNode):
            name: Optional[str] = None
            min_age: int = 18

        human = Human()

        assert len(human._checksums.keys()) == 2
        assert "name" in human._checksums
        assert human._checksums["name"] is None
        assert "min_age" in human._checksums
        assert isinstance(human._checksums["min_age"], str)

        assert human._id is None
        assert human.id is None

        assert human._element_id is None
        assert human.element_id is None

        assert human._hash is not None
