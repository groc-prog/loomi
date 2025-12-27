# pylint: disable=missing-class-docstring

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


class TestDirtyFields:
    def test_no_changes_does_nothing(self):
        """Verify that no changes to the fields results in no dirty fields."""

        class Human(LoomiNode):
            name: str
            age: int

        human = Human(name="John", age=24)
        assert len(human._dirty_fields.keys()) == 0

    def test_changes_are_tracked(self):
        """Verify that changes to the fields are tracked as dirty fields."""

        class Human(LoomiNode):
            name: str
            age: int

        human = Human(name="John", age=24)
        assert len(human._dirty_fields.keys()) == 0

        human.age = 26
        assert "age" in human._dirty_fields
        assert human._dirty_fields["age"] == 24

        human.age = 24
        assert len(human._dirty_fields.keys()) == 0


class TestFieldDefaults:
    def test_model_default_values(self):
        """Verify that a model is initialized with the correct defaults for graph related fields."""

        class Human(LoomiNode): ...

        human = Human()
        assert human._dirty_fields == {}
        assert human._id is None
        assert human.id is None
        assert human._element_id is None
        assert human.element_id is None
        assert human._hash is not None
