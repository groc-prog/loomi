# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import datetime
from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from loomi.exceptions import ModelError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.descriptors import FieldDescriptor
from loomi.query_api.functions.collection import all_, any_


class SimplePerson(Node):
    name: str
    age: int
    happy: bool
    balance: float


class NestedPersonMetadata(BaseModel):
    created_at: datetime.datetime


class NestedPersonSignup(BaseModel):
    metadata: NestedPersonMetadata
    complete: bool


class NestedPerson(Node):
    signup: NestedPersonSignup


class ListPropertyPersonHobbyMetadata(BaseModel):
    started_at: datetime.datetime
    milestones: List[str]


class ListPropertyPersonHobby(BaseModel):
    name: str
    metadata: ListPropertyPersonHobbyMetadata


class ListPropertyPerson(Node):
    hobbies: List[ListPropertyPersonHobby]


class DictPropertyPerson(Node):
    stages: Dict[str, bool]
    metadata: Dict[str, Any]


class TestFieldDescriptor:
    def test_raises_when_accessing_non_model_property(self):
        with pytest.raises(ModelError, match="invalid is not a valid field name for path name"):
            _ = SimplePerson.name.invalid  # type: ignore

    def test_returns_field_descriptor_when_accessing_class_property(self):
        name_descriptor = SimplePerson.name
        age_descriptor = SimplePerson.age
        happy_descriptor = SimplePerson.happy
        balance_descriptor = SimplePerson.balance

        assert isinstance(name_descriptor, FieldDescriptor)
        assert name_descriptor._annotation == str
        assert name_descriptor._model_type == SimplePerson
        assert name_descriptor._full_path == "name"

        assert isinstance(age_descriptor, FieldDescriptor)
        assert age_descriptor._annotation == int
        assert age_descriptor._model_type == SimplePerson
        assert age_descriptor._full_path == "age"

        assert isinstance(happy_descriptor, FieldDescriptor)
        assert happy_descriptor._annotation == bool
        assert happy_descriptor._model_type == SimplePerson
        assert happy_descriptor._full_path == "happy"

        assert isinstance(balance_descriptor, FieldDescriptor)
        assert balance_descriptor._annotation == float
        assert balance_descriptor._model_type == SimplePerson
        assert balance_descriptor._full_path == "balance"

    def test_returns_field_descriptor_for_nested_properties(self):
        nested_descriptor = NestedPerson.signup.complete
        deeply_nested_descriptor = NestedPerson.signup.metadata.created_at

        assert isinstance(nested_descriptor, FieldDescriptor)
        assert nested_descriptor._annotation == bool
        assert nested_descriptor._model_type == NestedPerson
        assert nested_descriptor._full_path == "signup.complete"

        assert isinstance(deeply_nested_descriptor, FieldDescriptor)
        assert deeply_nested_descriptor._annotation == datetime.datetime
        assert deeply_nested_descriptor._model_type == NestedPerson
        assert deeply_nested_descriptor._full_path == "signup.metadata.created_at"

    def test_returns_field_descriptor_for_list_properties(self):
        list_descriptor = any_(ListPropertyPerson.hobbies).name
        nested_list_descriptor = all_(any_(ListPropertyPerson.hobbies).metadata.milestones)

        assert isinstance(list_descriptor, FieldDescriptor)
        assert list_descriptor._annotation == str
        assert list_descriptor._model_type == ListPropertyPerson
        assert list_descriptor._full_path == "hobbies.$any.name"

        assert isinstance(nested_list_descriptor, FieldDescriptor)
        assert nested_list_descriptor._annotation == str
        assert nested_list_descriptor._model_type == ListPropertyPerson
        assert nested_list_descriptor._full_path == "hobbies.$any.metadata.milestones.$all"

    def test_list_properties_use_any_by_default(self):
        list_descriptor = ListPropertyPerson.hobbies.name  # type: ignore

        assert isinstance(list_descriptor, FieldDescriptor)
        assert list_descriptor._annotation == str
        assert list_descriptor._model_type == ListPropertyPerson
        assert list_descriptor._full_path == "hobbies.$any.name"

    def test_returns_field_descriptor_for_list_properties_when_accessed_by_index(self):
        list_descriptor = ListPropertyPerson.hobbies[2].name
        nested_list_descriptor = ListPropertyPerson.hobbies[0].metadata.milestones[1]

        assert isinstance(list_descriptor, FieldDescriptor)
        assert list_descriptor._annotation == str
        assert list_descriptor._model_type == ListPropertyPerson
        assert list_descriptor._full_path == "hobbies[2].name"

        assert isinstance(nested_list_descriptor, FieldDescriptor)
        assert nested_list_descriptor._annotation == str
        assert nested_list_descriptor._model_type == ListPropertyPerson
        assert nested_list_descriptor._full_path == "hobbies[0].metadata.milestones[1]"

    def test_returns_field_descriptor_for_dict_properties(self):
        dict_descriptor = DictPropertyPerson.stages["signup"]
        nested_dict_descriptor = DictPropertyPerson.metadata["timestamps"]["created_at"]

        assert isinstance(dict_descriptor, FieldDescriptor)
        assert dict_descriptor._annotation == bool
        assert dict_descriptor._model_type == DictPropertyPerson
        assert dict_descriptor._full_path == "stages.signup"

        assert isinstance(nested_dict_descriptor, FieldDescriptor)
        assert nested_dict_descriptor._annotation == Any
        assert nested_dict_descriptor._model_type == DictPropertyPerson
        assert nested_dict_descriptor._full_path == "metadata.timestamps.created_at"
