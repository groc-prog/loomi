# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import Annotated

import pytest

from loomi.exceptions import ModelError
from loomi.graph.annotations import (
    DataTypeConstraint,
    ExistenceConstraint,
    FullTextIndex,
    PointIndex,
    PropertyIndex,
    RangeIndex,
    TextIndex,
    UniquenessConstraint,
    VectorIndex,
    _JsonSchemaIndexOrConstraintType,
)
from loomi.graph.constraints import DataTypeConstraintType
from loomi.graph.node import Node


class TestUniquenessConstraint:
    def test_uniqueness_constraint_is_added_to_json_schema(self):
        """Verify that the constraint info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, UniquenessConstraint()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["composite_key"]
            is None
        )

    def test_uniqueness_constraint_persists_name(self):
        """Verify that the defined name for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, UniquenessConstraint(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"]
            == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["composite_key"]
            is None
        )

    def test_uniqueness_constraint_persists_labels(self):
        """Verify that the defined labels for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, UniquenessConstraint(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] == [
            "Human"
        ]

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["composite_key"]
            is None
        )

    def test_uniqueness_constraint_persists_composite_key(self):
        """Verify that the defined composite key for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, UniquenessConstraint(composite_key="my_composite_key")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["composite_key"]
            == "my_composite_key"
        )


class TestExistenceConstraint:
    def test_existence_constraint_is_added_to_json_schema(self):
        """Verify that the constraint info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, ExistenceConstraint()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.EXISTENCE_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

    def test_existence_constraint_persists_name(self):
        """Verify that the defined name for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, ExistenceConstraint(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.EXISTENCE_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"]
            == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

    def test_existence_constraint_persists_labels(self):
        """Verify that the defined labels for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, ExistenceConstraint(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.EXISTENCE_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] == [
            "Human"
        ]


class TestDataTypeConstraint:
    def test_data_type_constraint_is_added_to_json_schema(self):
        """Verify that the constraint info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, DataTypeConstraint(data_type=DataTypeConstraintType.STRING)]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.DATA_TYPE_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

        assert "data_type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["data_type"]
            == DataTypeConstraintType.STRING.value
        )

    def test_data_type_constraint_persists_name(self):
        """Verify that the defined name for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[
                str,
                DataTypeConstraint(data_type=DataTypeConstraintType.STRING, name="my_constraint"),
            ]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.DATA_TYPE_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"]
            == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] is None

        assert "data_type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["data_type"]
            == DataTypeConstraintType.STRING.value
        )

    def test_data_type_constraint_persists_labels(self):
        """Verify that the defined labels for the constraint is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[
                str,
                DataTypeConstraint(data_type=DataTypeConstraintType.STRING, labels=set(["Human"])),
            ]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "constraints" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["constraints"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.DATA_TYPE_CONSTRAINT.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert json_schema["properties"]["username"]["loomi"]["constraints"][0]["labels"] == [
            "Human"
        ]

        assert "data_type" in json_schema["properties"]["username"]["loomi"]["constraints"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["constraints"][0]["data_type"]
            == DataTypeConstraintType.STRING.value
        )


class TestPropertyIndex:
    def test_property_index_is_added_to_json_schema(self):
        """Verify that the index info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PropertyIndex()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.PROPERTY_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_property_index_persists_name(self):
        """Verify that the defined name for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PropertyIndex(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.PROPERTY_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_property_index_persists_labels(self):
        """Verify that the defined labels for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PropertyIndex(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.PROPERTY_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] == ["Human"]

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_property_index_persists_composite_key(self):
        """Verify that the defined composite key for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PropertyIndex(composite_key="my_composite_key")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.PROPERTY_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"]
            == "my_composite_key"
        )


class TestRangeIndex:
    def test_range_index_is_added_to_json_schema(self):
        """Verify that the index info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, RangeIndex()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.RANGE_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_range_index_persists_name(self):
        """Verify that the defined name for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, RangeIndex(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.RANGE_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_range_index_persists_labels(self):
        """Verify that the defined labels for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, RangeIndex(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.RANGE_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] == ["Human"]

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_range_index_persists_composite_key(self):
        """Verify that the defined composite key for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, RangeIndex(composite_key="my_composite_key")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.RANGE_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"]
            == "my_composite_key"
        )


class TestTextIndex:
    def test_text_index_is_added_to_json_schema(self):
        """Verify that the index info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, TextIndex()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

    def test_text_index_persists_name(self):
        """Verify that the defined name for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, TextIndex(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

    def test_text_index_persists_labels(self):
        """Verify that the defined labels for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, TextIndex(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] == ["Human"]


class TestPointIndex:
    def test_point_index_is_added_to_json_schema(self):
        """Verify that the index info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PointIndex()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.POINT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

    def test_point_index_persists_name(self):
        """Verify that the defined name for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PointIndex(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.POINT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

    def test_point_index_persists_labels(self):
        """Verify that the defined labels for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, PointIndex(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.POINT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] == ["Human"]


class TestFullTextIndex:
    def test_full_text_index_is_added_to_json_schema(self):
        """Verify that the index info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, FullTextIndex()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.FULL_TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_full_text_index_persists_name(self):
        """Verify that the defined name for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, FullTextIndex(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.FULL_TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_full_text_index_persists_labels(self):
        """Verify that the defined labels for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, FullTextIndex(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.FULL_TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] == ["Human"]

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"] is None

    def test_full_text_index_persists_composite_key(self):
        """Verify that the defined composite key for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, FullTextIndex(composite_key="my_composite_key")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.FULL_TEXT_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

        assert "composite_key" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["composite_key"]
            == "my_composite_key"
        )


class TestVectorIndex:
    def test_vector_index_is_added_to_json_schema(self):
        """Verify that the index info is added to the JSON schema output."""

        class Human(Node):
            username: Annotated[str, VectorIndex()]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.VECTOR_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

    def test_vector_index_persists_name(self):
        """Verify that the defined name for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, VectorIndex(name="my_constraint")]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.VECTOR_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] == "my_constraint"
        )

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] is None

    def test_vector_index_persists_labels(self):
        """Verify that the defined labels for the index is included in the JSON schema output."""

        class Human(Node):
            username: Annotated[str, VectorIndex(labels=set(["Human"]))]

        json_schema = Human.model_json_schema()
        assert "properties" in json_schema
        assert "username" in json_schema["properties"]
        assert "loomi" in json_schema["properties"]["username"]
        assert "indexes" in json_schema["properties"]["username"]["loomi"]
        assert len(json_schema["properties"]["username"]["loomi"]["indexes"]) == 1

        assert "type" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert (
            json_schema["properties"]["username"]["loomi"]["indexes"][0]["type"]
            is _JsonSchemaIndexOrConstraintType.VECTOR_INDEX.value
        )

        assert "name" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["name"] is None

        assert "labels" in json_schema["properties"]["username"]["loomi"]["indexes"][0]
        assert json_schema["properties"]["username"]["loomi"]["indexes"][0]["labels"] == ["Human"]
