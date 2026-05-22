# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import json
from typing import List, Optional, Set
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, ValidationError

from loomi.constants import ServerType
from loomi.exceptions import SerializationError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class TestModelHash:

    def test_hash_with_same_inputs_has_different_result_with_different_entity(self):
        """
        Verify that same inputs for node and relationship model hashes result in different
        strings.
        """

        class Human(Node): ...

        class Likes(Relationship): ...

        hash_1 = Human._generate_hash(set("input"))  # type: ignore
        hash_2 = Likes._generate_hash(set("input"))  # type: ignore
        assert hash_1 != hash_2


class TestEqualsMagicMethod:

    def test_different_entities_are_not_equal(self):
        """
        Verify that entities of the same type with different element ids are not equal.
        """

        class Human(Node): ...

        class NotAModel: ...

        assert Human() == Human()
        assert Human() != NotAModel()

        human1 = Human()
        human1._element_id = "element_id_1"

        human2 = Human()
        human2._element_id = "element_id_2"

        assert human1 != human2


class TestFieldDefaults:
    def test_model_default_values(self):
        """Verify that a model is initialized with the correct defaults for graph related fields."""

        class Human(Node):
            name: Optional[str] = None
            min_age: int = 18

        human = Human()

        assert human._id is None
        assert human.id is None

        assert human._element_id is None
        assert human.element_id is None

        assert human._hash is not None


class TestSerialize:
    def test_serializes_supported_values_to_python_dict(self):
        """
        Verify that supported python primitive types are serializes to a python dict.
        """

        class Human(Node):
            name: str
            age: int
            jobs: List[str]
            alive: bool

        human = Human(name="John", age=21, jobs=["Developer", "Engineer", "Farmer"], alive=True)
        serialized = human._serialize(ServerType.NEO4J, {})

        assert "name" in serialized
        assert serialized["name"] == "John"

        assert "age" in serialized
        assert serialized["age"] == 21

        assert "jobs" in serialized
        assert serialized["jobs"] == ["Developer", "Engineer", "Farmer"]

        assert "alive" in serialized
        assert serialized["alive"] is True

    def test_serializes_nested_dict_values(self):
        """
        Verify that nested dict values are serialized if serialize_nested is set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: Metadata = Metadata()

        human = Human()
        serialized = human._serialize(ServerType.NEO4J, {"serialize_nested": True})

        assert "metadata" in serialized
        assert isinstance(serialized["metadata"], str)
        assert serialized["metadata"] == json.dumps({"field": "value"})

    def test_serializes_nested_dict_list_items(self):
        """
        Verify that nested dict values in lists are serialized if serialize_nested is set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: List[Metadata] = [Metadata()]

        human = Human()
        serialized = human._serialize(ServerType.NEO4J, {"serialize_nested": True})

        assert "metadata" in serialized
        assert isinstance(serialized["metadata"], list)
        assert len(serialized["metadata"]) == 1
        assert serialized["metadata"][0] == json.dumps({"field": "value"})

    def test_raises_if_serializer_function_not_defined(self):
        """Verify that a error is thrown if no serializer function is provided."""

        class Human(Node): ...

        Human.loomi_config.pop("serializer_fn")

        human = Human()
        with pytest.raises(SerializationError):
            human._serialize(ServerType.NEO4J, {})

    def test_raises_if_non_supported_datatype_is_found(self):
        """
        Verify that a error is thrown if a not supported datatype is present in the dumped object.
        """

        class Human(Node):
            values: UUID

        human = Human(values=uuid4())
        with pytest.raises(SerializationError):
            human._serialize(ServerType.NEO4J, {})

    def test_raises_if_non_supported_list_datatype_is_found(self):
        """
        Verify that a error is thrown if a not supported datatype is present in the dumped object.
        """

        class Human(Node):
            values: List[Set[str]]

        human = Human(values=[set(["a", "b"])])
        with pytest.raises(SerializationError):
            human._serialize(ServerType.NEO4J, {})

    def test_raises_if_nested_dict_is_found_with_missing_setting(self):
        """
        Verify that a error is thrown if a nested dict is found, but serialize_nested is not set to
        True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: Metadata = Metadata()

        human = Human()
        with pytest.raises(SerializationError):
            human._serialize(ServerType.NEO4J, {})

    def test_raises_if_nested_list_is_found_with_missing_setting(self):
        """
        Verify that a error is thrown if a nested dict in a list is found, but serialize_nested
        is not set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: List[Metadata] = [Metadata()]

        human = Human()
        with pytest.raises(SerializationError):
            human._serialize(ServerType.NEO4J, {})

    def test_raises_if_custom_serialization_function_raises(self):
        """
        Verify that a error is thrown if a custom serialization function throws.
        """

        def serialization_fn():
            raise RuntimeError("failure")

        class Metadata(BaseModel):
            field: str = "value"

        class HumanNestedDict(Node):
            metadata: Metadata = Metadata()

            loomi_config = {"serializer_fn": serialization_fn}  # type: ignore

        class HumanNestedList(Node):
            metadata: List[Metadata] = [Metadata()]

            loomi_config = {"serializer_fn": serialization_fn}  # type: ignore

        with pytest.raises(SerializationError):
            human = HumanNestedDict()
            human._serialize(ServerType.NEO4J, {"serialize_nested": True})

        with pytest.raises(SerializationError):
            human = HumanNestedList()
            human._serialize(ServerType.NEO4J, {"serialize_nested": True})


class TestDeserialize:
    def test_deserializes_dict_to_model(self):
        """
        Verify that dicts are correctly deserializes into models.
        """

        class Human(Node):
            name: str
            age: int
            jobs: List[str]
            alive: bool

        human = Human._deserialize(
            {"name": "John", "age": 21, "jobs": ["Developer", "Engineer", "Farmer"], "alive": True},
            ServerType.NEO4J,
            {},
        )

        assert human.name == "John"
        assert human.age == 21
        assert human.jobs == ["Developer", "Engineer", "Farmer"]
        assert human.alive is True

    def test_deserializes_nested_dict_values(self):
        """
        Verify that nested dict values are deserialized if serialize_nested is set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: Metadata

        human = Human._deserialize(
            {"metadata": json.dumps({"field": "value"})},
            ServerType.NEO4J,
            {"serialize_nested": True},
        )

        assert human.metadata == Metadata(field="value")

    def test_deserializes_nested_dict_list_items(self):
        """
        Verify that nested dict values in lists are deserialized if serialize_nested is set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: List[Metadata]

        human = Human._deserialize(
            {"metadata": [json.dumps({"field": "value"})]},
            ServerType.NEO4J,
            {"serialize_nested": True},
        )

        assert human.metadata == [Metadata(field="value")]

    def test_raises_if_deserializer_function_not_defined(self):
        """Verify that a error is thrown if no deserializer function is provided."""

        class Human(Node): ...

        Human.loomi_config.pop("deserializer_fn")

        with pytest.raises(SerializationError):
            Human._deserialize({}, ServerType.NEO4J, {})

    def test_skips_unknown_fields(self):
        """
        Verify that unknown keys from dicts are ignored when deserializing into a model.
        """

        class Human(Node):
            name: str
            age: int

        human = Human._deserialize(
            {
                "name": "John",
                "age": 21,
                "jobs": ["Developer", "Engineer", "Farmer"],
            },
            ServerType.NEO4J,
            {},
        )

        assert human.name == "John"
        assert human.age == 21

    def test_raises_if_stringified_nested_dict_is_found_with_missing_setting(self):
        """
        Verify that a error is thrown if a stringified nested dict is found, but serialize_nested
        is not set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: Metadata

        with pytest.raises(ValidationError):
            Human._deserialize({"metadata": json.dumps({"field": "value"})}, ServerType.NEO4J, {})

    def test_raises_if_stringified_nested_list_is_found_with_missing_setting(self):
        """
        Verify that a error is thrown if a stringified nested dict in a list is found, but
        serialize_nested is not set to True.
        """

        class Metadata(BaseModel):
            field: str = "value"

        class Human(Node):
            metadata: List[Metadata]

        with pytest.raises(ValidationError):
            Human._deserialize({"metadata": [json.dumps({"field": "value"})]}, ServerType.NEO4J, {})

    def test_raises_if_custom_deserialization_function_raises(self):
        """
        Verify that a error is thrown if a custom deserialization function throws.
        """

        def deserialization_fn():
            raise RuntimeError("failure")

        class Metadata(BaseModel):
            field: str = "value"

        class HumanNestedDict(Node):
            metadata: Metadata

            loomi_config = {"deserializer_fn": deserialization_fn}  # type: ignore

        class HumanNestedList(Node):
            metadata: List[Metadata] = [Metadata()]

            loomi_config = {"deserializer_fn": deserialization_fn}  # type: ignore

        with pytest.raises(SerializationError):
            HumanNestedDict._deserialize(
                {"metadata": json.dumps({"field": "value"})},
                ServerType.NEO4J,
                {"serialize_nested": True},
            )

        with pytest.raises(SerializationError):
            HumanNestedList._deserialize(
                {"metadata": [json.dumps({"field": "value"})]},
                ServerType.NEO4J,
                {"serialize_nested": True},
            )
