# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import pytest

from loomi.exceptions import ModelError
from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.descriptors import FieldDescriptor


class Human(Node):
    name: str


class TestAlias:
    def test_alias_raises_if_using_reserved_name(self):
        with pytest.raises(ModelError):
            create_alias(Human, "v0")

    def test_alias_exposes_field_descriptor(self):
        alias = create_alias(Human, "human")

        descriptor = alias.name
        assert isinstance(descriptor, FieldDescriptor)
        assert descriptor._full_path == "name"
        assert descriptor._model_type == alias

    def test_alias_raises_when_not_accessing_field(self):
        alias = create_alias(Human, "human")

        with pytest.raises(ModelError):
            _ = alias.element_id
