from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional, Set

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

from loomi.graph.constraints import DataTypeConstraintType


class _JsonSchemaIndexOrConstraintType(StrEnum):
    UNIQUENESS_CONSTRAINT = "uniqueness_constraint"
    EXISTENCE_CONSTRAINT = "existence_constraint"
    DATA_TYPE_CONSTRAINT = "data_type_constraint"
    PROPERTY_INDEX = "property_index"
    RANGE_INDEX = "range_index"
    TEXT_INDEX = "text_index"
    POINT_INDEX = "point_index"
    FULL_TEXT_INDEX = "full_text_index"
    VECTOR_INDEX = "vector_index"


@dataclass(frozen=True)
class _IndexOrConstraintMetadata:
    type: _JsonSchemaIndexOrConstraintType
    name: Optional[str]
    labels: Optional[Set[str]]
    composite_key: Optional[str]
    data_type: Optional[DataTypeConstraintType]


@dataclass
class UniquenessConstraint:
    """Annotation for creating a uniqueness constraint for a field."""

    composite_key: Optional[str] = None
    """Composite key used to include multiple fields in the same constraint."""
    name: Optional[str] = None
    """Name for the constraint. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the constraint will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_constraint"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT,
            self.name,
            self.labels if self.labels else None,
            self.composite_key,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_constraint` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_constraint")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["constraints"].append(constraint_metadata)

        return json_schema


@dataclass
class ExistenceConstraint:
    """
    Annotation for creating a existence constraint for a field.

    [!NOTE] This constraint is only available for Memgraph.
    """

    name: Optional[str] = None
    """Name for the constraint. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the constraint will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_constraint"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.EXISTENCE_CONSTRAINT,
            self.name,
            self.labels if self.labels else None,
            None,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_constraint` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_constraint")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["constraints"].append(constraint_metadata)

        return json_schema


@dataclass
class DataTypeConstraint:
    """
    Annotation for creating a data type constraint for a field.

    [!NOTE] This constraint is only available for Memgraph.
    """

    data_type: DataTypeConstraintType
    """The type used for the data type constraint."""
    name: Optional[str] = None
    """Name for the constraint. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the constraint will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_constraint"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.DATA_TYPE_CONSTRAINT,
            self.name,
            self.labels if self.labels else None,
            None,
            self.data_type,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_constraint` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_constraint")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["constraints"].append(constraint_metadata)

        return json_schema


@dataclass
class PropertyIndex:
    """
    Annotation for creating a property index for a field.

    [!NOTE] This index is only available for Memgraph.
    """

    composite_key: Optional[str] = None
    """Composite key used to include multiple fields in the same index."""
    name: Optional[str] = None
    """Name for the index. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the index will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_index"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.PROPERTY_INDEX,
            self.name,
            self.labels if self.labels else None,
            self.composite_key,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_index` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_index")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["indexes"].append(constraint_metadata)

        return json_schema


@dataclass
class RangeIndex:
    """
    Annotation for creating a range index for a field.

    [!NOTE] This index is only available for Neo4j.
    """

    composite_key: Optional[str] = None
    """Composite key used to include multiple fields in the same index."""
    name: Optional[str] = None
    """Name for the index. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the index will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_index"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.RANGE_INDEX,
            self.name,
            self.labels if self.labels else None,
            self.composite_key,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_index` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_index")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["indexes"].append(constraint_metadata)

        return json_schema


@dataclass
class TextIndex:
    """
    Annotation for creating a text index for a field.

    [!NOTE] This index is only available for Neo4j.
    """

    name: Optional[str] = None
    """Name for the index. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the index will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_index"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.TEXT_INDEX,
            self.name,
            self.labels if self.labels else None,
            None,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_index` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_index")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["indexes"].append(constraint_metadata)

        return json_schema


@dataclass
class PointIndex:
    """
    Annotation for creating a point index for a field.
    """

    name: Optional[str] = None
    """Name for the index. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the index will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_index"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.POINT_INDEX,
            self.name,
            self.labels if self.labels else None,
            None,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_index` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_index")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["indexes"].append(constraint_metadata)

        return json_schema


@dataclass
class FullTextIndex:
    """
    Annotation for creating a full-text index for a field.

    [!NOTE] This index is only available for Neo4j.
    """

    composite_key: Optional[str] = None
    """Composite key used to include multiple fields in the same index."""
    name: Optional[str] = None
    """Name for the index. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the index will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_index"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.FULL_TEXT_INDEX,
            self.name,
            self.labels if self.labels else None,
            self.composite_key,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_index` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_index")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["indexes"].append(constraint_metadata)

        return json_schema


@dataclass
class VectorIndex:
    """
    Annotation for creating a vector index for a field.

    [!NOTE] This index is only available for Neo4j.
    """

    name: Optional[str] = None
    """Name for the index. Will be auto generated if not defined."""
    labels: Optional[Set[str]] = None
    """
    Labels for which the index will be created. Will be created for all labels
    if not defined.
    """

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        # 1. Get the base schema
        base_schema = handler(source_type)
        base_schema.setdefault("metadata", {})["loomi_index"] = _IndexOrConstraintMetadata(
            _JsonSchemaIndexOrConstraintType.VECTOR_INDEX,
            self.name,
            self.labels if self.labels else None,
            None,
            None,
        )

        return base_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(_core_schema)

        # The metadata in the core schema should have the `loomi_index` key we
        # set earlier
        constraint_metadata = _core_schema.get("metadata", {}).get("loomi_index")

        if constraint_metadata:
            loomi_meta = json_schema.setdefault("loomi", {"indexes": [], "constraints": []})
            loomi_meta["indexes"].append(constraint_metadata)

        return json_schema
