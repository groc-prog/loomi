# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable
import json

import pytest
from pydantic import BaseModel

from loomi.exceptions import ModelError
from loomi.graph.relationship import Relationship
from loomi.query_api._core.descriptors import FieldDescriptor


class TestRelationshipModelFields:
    def test_relationship_exposes_field_descriptors_on_class_field_paths(self):
        class Likes(Relationship):
            name: str

        descriptor = Likes.name
        assert isinstance(descriptor, FieldDescriptor)

    def test_relationship_raises_when_type_not_available(self):
        class Likes(Relationship): ...

        Likes.loomi_config["type"] = None  # type: ignore

        with pytest.raises(
            ModelError,
            match=f"Type on model {Likes.__name__} is not initialized. Maybe you forgot to call {Likes.model_rebuild.__name__}?",
        ):
            Likes.type()


class TestRelationshipMagicMethods:
    def test_relationship_must_have_same_type_and_element_id_to_be_equal(self):
        class Likes(Relationship): ...

        class Loves(Relationship): ...

        likes1 = Likes()
        likes2 = Likes()

        likes3 = Likes()
        likes3._element_id = "4:ff04df25-ff2b-4b55-98f8-6888297b025e:0"

        likes4 = Likes()
        likes4._element_id = "4:ff04df25-ff2b-4b55-98f8-6888297b025e:42"

        loves = Loves()

        assert likes1 == likes2
        assert (likes1 == likes3) is False
        assert (likes3 == likes4) is False
        assert (likes1 == loves) is False


class TestRelationshipModelConfiguration:
    def test_relationship_uses_class_name_as_default_type(self):
        class Likes(Relationship): ...

        assert "type" in Likes.loomi_config
        assert Likes.loomi_config["type"] == "LIKES"
        assert Likes.type() == "LIKES"

    def test_relationship_uses_defined_type(self):
        class Likes(Relationship):
            loomi_config = {"type": "REALLY_LIKES"}

        assert "type" in Likes.loomi_config
        assert Likes.loomi_config["type"] == "REALLY_LIKES"
        assert Likes.type() == "REALLY_LIKES"

    def test_relationship_inherits_type_from_parent_relationships(self):
        class Metadata(BaseModel): ...

        class Likes(Relationship): ...

        class ReallyLikes(Relationship): ...

        class Loves(Likes, ReallyLikes, Metadata): ...

        assert "type" in Loves.loomi_config
        assert Loves.loomi_config["type"] == "LOVES"
        assert Loves.type() == "LOVES"

    def test_relationship_inherits_type_from_parent_relationship_and_defines_own_type(self):
        class Likes(Relationship): ...

        class Loves(Likes):
            loomi_config = {"type": "REALLY_LOVES"}

        assert "type" in Loves.loomi_config
        assert Loves.loomi_config["type"] == "REALLY_LOVES"
        assert Loves.type() == "REALLY_LOVES"
