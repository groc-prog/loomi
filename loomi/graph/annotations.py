from dataclasses import dataclass
from typing import Optional, Set

from loomi.graph.constraints import DataTypeConstraintType

# TODO: These are currently unused and will be used when implementing
# migrations


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
