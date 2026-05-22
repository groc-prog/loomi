from typing import Any, Dict, List, Optional, Set, cast

import xxhash
from pydantic import BaseModel

from loomi._internal.base_model import _JsonSchemaModelType, _ModelSchemaMetadata
from loomi._internal.types import ModelType
from loomi._logger import LogContextKey, logger, scoped_log_ctx
from loomi.exceptions import MigrationError
from loomi.graph.annotations import _IndexOrConstraintMetadata, _JsonSchemaIndexOrConstraintType
from loomi.graph.constraints import DataTypeConstraintType
from loomi.graph.node import Node


class IndexOrConstraintDefinition(BaseModel):
    """Index/constraint definition for a model."""

    type: _JsonSchemaIndexOrConstraintType
    name: Optional[str]
    labels_or_type: Set[str]
    data_type: Optional[DataTypeConstraintType]
    properties: Set[str]


class PropertyDefinition(BaseModel):
    """Property definition for a model."""

    type: str
    format: Optional[str]
    default_value: Optional[Any]


class MigrationSchemaDefinition(BaseModel):
    """Model definition for a migration."""

    model_type: _JsonSchemaModelType
    labels_or_type: Set[str]
    properties: Dict[str, PropertyDefinition]
    indexes: Dict[str, IndexOrConstraintDefinition]
    constraints: Dict[str, IndexOrConstraintDefinition]


class MigrationSchemaFactory:
    """
    Factory class for generation migration schema definitions for the current
    provided model.
    """

    _model: ModelType

    def __init__(self, model: ModelType) -> None:
        self._model = model

    def generate_schema_definition(self) -> MigrationSchemaDefinition:
        """
        Generates a migrations schema definition for the current model. The resulting
        definition includes all properties and all top-level indexes and constraints.

        Returns:
            MigrationSchemaDefinition: The migration definition for the current model.
        """
        model_schema = self._model.model_json_schema()

        properties: Dict[str, PropertyDefinition] = {}
        indexes: List[IndexOrConstraintDefinition] = []
        composite_indexes: Dict[str, IndexOrConstraintDefinition] = {}
        constraints: List[IndexOrConstraintDefinition] = []
        composite_constraints: Dict[str, IndexOrConstraintDefinition] = {}

        model_metadata: Optional[_ModelSchemaMetadata] = model_schema.get("loomi")
        if model_metadata is None or model_metadata.hash is None:
            raise MigrationError("Model schema metadata not found")

        with scoped_log_ctx({LogContextKey.MODEL_IDENTIFIER: model_metadata.hash}):
            logger.debug("Generating model definition for properties, indexes and constraints")

            model_properties: Dict[str, Any] = model_schema.get("properties", {})
            logger.debug("Found %d properties in model schema", len(model_properties.keys()))
            for property_name, property_ in model_properties.items():
                if not isinstance(property_, dict):
                    raise MigrationError(f"Property {property_name} is not a valid dict")

                default_value = property_.get("default")
                properties.setdefault(
                    property_name,
                    PropertyDefinition(
                        type=cast(str, property_.get("type")),
                        format=property_.get("format"),
                        default_value=default_value,
                    ),
                )
                logger.debug(
                    "Added definition for property %s with default value %s",
                    property_name,
                    default_value,
                )

                property_metadata: Dict[str, Any] = property_.get("loomi", {})
                if property_metadata:
                    self._get_index_or_constraint_definitions(
                        model_metadata,
                        property_name,
                        property_metadata.get("indexes", []),
                        indexes,
                        composite_indexes,
                    )
                    self._get_index_or_constraint_definitions(
                        model_metadata,
                        property_name,
                        property_metadata.get("constraints", []),
                        constraints,
                        composite_constraints,
                    )

        return MigrationSchemaDefinition(
            model_type=(
                _JsonSchemaModelType.NODE
                if issubclass(self._model, Node)
                else _JsonSchemaModelType.RELATIONSHIP
            ),
            labels_or_type=(
                self._model._get_labels()
                if issubclass(self._model, Node)
                else set([self._model._get_type()])
            ),
            properties=properties,
            indexes=self._generate_index_or_constraint_hash(
                [*indexes, *composite_indexes.values()]
            ),
            constraints=self._generate_index_or_constraint_hash(
                [*constraints, *composite_constraints.values()]
            ),
        )

    def _get_index_or_constraint_definitions(
        self,
        model_metadata: _ModelSchemaMetadata,
        property_name: str,
        property_indexes_or_constraints: List[_IndexOrConstraintMetadata],
        indexes_or_constraints_definition: List[IndexOrConstraintDefinition],
        composite_indexes_or_constraints_definition: Dict[str, IndexOrConstraintDefinition],
    ) -> None:
        logger.debug(
            "Found %d indexes/constraints for property %s",
            len(property_indexes_or_constraints),
            property_name,
        )
        for index_or_constraint_metadata in property_indexes_or_constraints:
            if (
                model_metadata.type == _JsonSchemaModelType.NODE
                and model_metadata.labels
                and index_or_constraint_metadata.labels
            ):
                # Check if the index or constraint defines any labels which the node does
                # not define itself and throw if one is found
                invalid_labels = index_or_constraint_metadata.labels - model_metadata.labels
                if len(invalid_labels) != 0:
                    raise MigrationError(
                        f"Invalid labels {', '.join(invalid_labels)} found. Only labels defined on "
                        "itself can be defined for indexes or constraints the model"
                    )

            applied_labels_or_type: Set[str] = set()
            if model_metadata.model_type == _JsonSchemaModelType.NODE:
                if index_or_constraint_metadata.labels:
                    applied_labels_or_type.update(index_or_constraint_metadata.labels)
                else:
                    applied_labels_or_type.update(cast(Set[str], model_metadata.labels))

                logger.debug("Using labels %s", applied_labels_or_type)
            else:
                applied_labels_or_type.add(model_metadata.model_type)
                logger.debug("Using type %s", applied_labels_or_type)

            composite_key = index_or_constraint_metadata.composite_key
            if composite_key:
                # Since composite keys stretch across multiple properties, we have to group them by
                # their composite key and can only generate the final definition later on
                composite_indexes_or_constraints_definition.setdefault(
                    composite_key,
                    IndexOrConstraintDefinition(
                        type=index_or_constraint_metadata.type,
                        name=index_or_constraint_metadata.name,
                        labels_or_type=applied_labels_or_type,
                        data_type=index_or_constraint_metadata.data_type,
                        properties=set([property_name]),
                    ),
                )

                if composite_key in composite_indexes_or_constraints_definition:
                    composite_name = composite_indexes_or_constraints_definition[composite_key].name
                    data_type = composite_indexes_or_constraints_definition[composite_key].data_type

                    # The same composite key can not define different names for the index/constraint
                    # to use
                    if (
                        index_or_constraint_metadata.name is not None
                        and composite_name is not None
                        and index_or_constraint_metadata.name != composite_name
                    ):
                        raise MigrationError(
                            "Index or constraint name can not be different for the same composite "
                            "index or constraint"
                        )

                    # Likewise, the same constraint can also not define different data types
                    if (
                        index_or_constraint_metadata.data_type is not None
                        and data_type is not None
                        and index_or_constraint_metadata.data_type != data_type
                    ):
                        raise MigrationError(
                            "Index or constraint data type can not be different for the same "
                            "composite index or constraint"
                        )

                    composite_indexes_or_constraints_definition[composite_key].name = (
                        index_or_constraint_metadata.name
                    )
                    composite_indexes_or_constraints_definition[composite_key].data_type = (
                        index_or_constraint_metadata.data_type
                    )
                    composite_indexes_or_constraints_definition[
                        composite_key
                    ].labels_or_type.update(applied_labels_or_type)
                    composite_indexes_or_constraints_definition[composite_key].properties.add(
                        property_name
                    )

                continue

            indexes_or_constraints_definition.append(
                IndexOrConstraintDefinition(
                    type=index_or_constraint_metadata.type,
                    name=index_or_constraint_metadata.name,
                    labels_or_type=applied_labels_or_type,
                    data_type=index_or_constraint_metadata.data_type,
                    properties=set([property_name]),
                )
            )

    def _generate_index_or_constraint_hash(
        self,
        definitions: List[IndexOrConstraintDefinition],
    ) -> Dict[str, IndexOrConstraintDefinition]:
        hashed: Dict[str, IndexOrConstraintDefinition] = {}

        for definition in definitions:
            hash_key = xxhash.xxh64(definition.model_dump_json()).hexdigest()
            hashed[hash_key] = definition

        return hashed
