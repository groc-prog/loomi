from typing import Any, Dict, List, Optional

from loomi._internal.base_model import _JsonSchemaModelType
from loomi._logger import logger
from loomi.graph.annotations import _JsonSchemaIndexOrConstraintType
from loomi.migrations._schema import IndexOrConstraintDefinition, MigrationSchemaDefinition
from loomi.migrations.settings import MigrationSettings


class MigrationComparer:
    """
    Generates Cypher migration queries by comparing a source and target
    MigrationSchemaDefinition for a specific model.
    """

    migration_content: List[str]

    _settings: MigrationSettings
    _previous_schema: Dict[str, MigrationSchemaDefinition]
    _current_schema: Dict[str, MigrationSchemaDefinition]

    def __init__(
        self,
        settings: MigrationSettings,
        previous_schema: Dict[str, MigrationSchemaDefinition],
        current_schema: Dict[str, MigrationSchemaDefinition],
    ):
        self.migration_content = []

        self._settings = settings
        self._previous_schema = previous_schema
        self._current_schema = current_schema

    def _compare_properties(
        self,
        previous_schema_definition: MigrationSchemaDefinition,
        current_schema_definition: MigrationSchemaDefinition,
    ) -> None:
        logger.debug("Comparing properties for changes")
        previous_properties = set(previous_schema_definition.properties.keys())
        current_properties = set(current_schema_definition.properties.keys())

        removed_properties = previous_properties - current_properties
        if len(removed_properties) > 0:
            logger.debug("Found %d removed properties", len(removed_properties))
            for property_name in removed_properties:
                match_query = self._get_match_query(previous_schema_definition)
                self.migration_content.append(f"{match_query} REMOVE e.{property_name}")

        new_or_changed_properties = current_properties - previous_properties
        if len(new_or_changed_properties) > 0:
            logger.debug("Found %d new or changed properties", len(new_or_changed_properties))
            for property_name in new_or_changed_properties:
                property_definition = current_schema_definition.properties[property_name]
                if property_definition.default_value is None:
                    continue

                logger.debug(
                    "Property %s has a default value defined, compiling query", property_name
                )
                match_query = self._get_match_query(current_schema_definition)
                value = (
                    property_definition.default_value
                    if not isinstance(property_definition.default_value, str)
                    else f"'{property_definition.default_value}'"
                )
                self.migration_content.append(f"{match_query} SET e.{property_name} = {value}")

        same_properties = current_properties & previous_properties
        if len(same_properties) > 0:
            logger.debug("Found %d properties which remained the same", len(same_properties))
            for property_name in same_properties:
                previous_type = previous_schema_definition.properties[property_name].type
                current_type = current_schema_definition.properties[property_name].type

                if previous_type == current_type:
                    continue

                match_query = self._get_match_query(current_schema_definition)

                logger.debug("Property %s changed its data type, compiling query", property_name)
                match current_type:
                    case "boolean":
                        self.migration_content.append(
                            f"{match_query} SET e.{property_name} = toBoolean(e.{property_name})"
                        )
                    case "integer":
                        self.migration_content.append(
                            f"{match_query} SET e.{property_name} = toInteger(e.{property_name})"
                        )
                    case "number":
                        self.migration_content.append(
                            f"{match_query} SET e.{property_name} = toFloat(e.{property_name})"
                        )
                    case "string":
                        transformed = self._get_str_format_transformation(
                            property_name,
                            current_schema_definition.properties[property_name].format,
                        )
                        self.migration_content.append(
                            f"{match_query} SET e.{property_name} = {transformed}"
                        )
                    case _:
                        # Some data types (lists, dicts, etc) can not be transformed automatically
                        # Instead, we add a comment here to indicate possible breaking changes
                        self.migration_content.append(
                            (
                                f"// TODO (Migration): `{property_name}` was not transformed "
                                "automatically after data type change. Please manually review "
                                "how you want to map this."
                            )
                        )

    def _get_str_format_transformation(self, property_name: str, format_: Optional[str]) -> str:
        match format_:
            case "date":
                return f"date(e.{property_name})"
            case "date-time":
                return f"datetime(e.{property_name})"
            case "time":
                return f"time(e.{property_name})"
            case "duration":
                return f"duration(e.{property_name})"
            case _:
                return f"toString(e.{property_name})"

    def _get_match_query(self, schema_definition: MigrationSchemaDefinition) -> str:
        if schema_definition.model_type == _JsonSchemaModelType.NODE:
            return f"MATCH (e:{':'.join(schema_definition.labels_or_type)})"

        return f"MATCH ()-[e:{':'.join(schema_definition.labels_or_type)}]-()"
