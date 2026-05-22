# pylint: disable=line-too-long

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, LiteralString, Optional, Set, Tuple, cast

import neo4j
import xxhash
from pydantic import BaseModel

from loomi._internal.base_model import _JsonSchemaModelType, _ModelSchemaMetadata
from loomi._logger import logger
from loomi.exceptions import MigrationError
from loomi.graph.annotations import _IndexOrConstraintMetadata, _JsonSchemaIndexOrConstraintType
from loomi.graph.constraints import DataTypeConstraintType
from loomi.migrations.settings import MigrationSettings

_CompositeIndexesOrConstraints = Dict[str, "_IndexOrConstraintDefinition"]
_IndexesOrConstraints = List["_IndexOrConstraintDefinition"]


class _IndexOrConstraintDefinition(BaseModel):
    type: _JsonSchemaIndexOrConstraintType
    name: Optional[str]
    labels_or_type: Set[str]
    data_type: Optional[DataTypeConstraintType]
    properties: Set[str]


def generate_migration_file(name: str, settings: MigrationSettings) -> Path:
    """
    Generates a new migration file from the difference in loomi models.

    Args:
        name (str): The name of the migration.
        settings (MigrationSettings): The settings for generating the migration.

    Raises:
        MigrationError: If the path where migrations are stored is not a valid directory.

    Returns:
        Path: The path of the generated file.
    """
    migration_files_dir = settings.migration_dir / "versions"

    if not migration_files_dir.exists():
        logger.debug("Migration files directory does not exist, creating new directory")
        migration_files_dir.mkdir(parents=True, exist_ok=True)

    if not migration_files_dir.is_dir():
        raise MigrationError(f"The path '{migration_files_dir}' exists but is not a directory.")

    timestamp = datetime.now().timestamp()
    migration_name = f"{timestamp}_{name}"
    migration_file_path = migration_files_dir / f"{migration_name}.cypher"
    snapshot_file_path = settings.migration_dir / "snapshot.json"

    last_migration_file: Optional[Path] = None
    existing_migration_files = sorted(list(migration_files_dir.glob("*.cypher")))
    if len(existing_migration_files) != 0:
        last_migration_file = existing_migration_files[-1]
        logger.debug("Identifier last created migration as %s", last_migration_file)
    else:
        logger.debug("No prior migration files found")

    labels = ":".join(settings.migration_node_labels)
    with migration_file_path.open("a") as file:
        # TODO: Generate actual migration content
        if last_migration_file:
            file.write(
                f"\nMATCH (m:{labels}) WHERE m.name = '{last_migration_file.stem}' "
                f"CREATE (m)-[:{settings.migration_relationship_type}]->(mn:{labels} {{name: '{migration_name}'}})"
            )
        else:
            file.write(f"\nCREATE (mn:{labels} {{name: '{migration_name}'}})")

    with snapshot_file_path.open("a") as file:
        json.dump({}, file, indent=4)

    return migration_file_path


def apply_pending_migration(settings: MigrationSettings) -> Tuple[int, Optional[str]]:
    """
    Applies all pending migrations.

    Args:
        settings (MigrationSettings): The settings for generating the migration.

    Raises:
        MigrationError: If the settings do not define a database DSN string.

    Returns:
        Tuple[int, Optional[str]]: The number of applied migrations and the first failing migration,
        if there is any.
    """
    migration_files_dir = settings.migration_dir / "versions"
    existing_migration_files = sorted(list(migration_files_dir.glob("*.cypher")))

    if len(existing_migration_files) == 0:
        logger.debug("No migration files found, nothing to do")
        return (0, None)

    if settings.db_dsn is None:
        raise MigrationError("No database DSN provided")

    if settings.server_type is None:
        raise MigrationError("No database server type provided")

    driver = neo4j.GraphDatabase.driver(settings.db_dsn)
    labels = ":".join(settings.migration_node_labels)

    last_migration_name: Optional[str] = None
    with driver.session() as session:
        query = f"MATCH (m:{labels}) WHERE NOT (m)-->() RETURN m.name"
        result = session.run(cast(LiteralString, query))
        record = result.single()

        if record is not None:
            last_migration_name = record.get("name", None)

    migrations_to_apply: List[Path] = []
    if last_migration_name:
        last_migration_idx = [file.stem for file in existing_migration_files].index(
            last_migration_name
        )
        migrations_to_apply = existing_migration_files[last_migration_idx + 1 :]

        if len(migrations_to_apply) == 0:
            logger.debug("No pending migrations found, skipping")
            return (0, None)
    else:
        migrations_to_apply = existing_migration_files
        logger.debug("Found %d migrations to apply", len(migrations_to_apply))

    with driver.session() as session:
        for index, migration_file in enumerate(migrations_to_apply):
            logger.debug("Applying migration %s", migration_file)
            try:
                with session.begin_transaction() as tx:
                    query = migration_file.read_text(encoding="utf-8")
                    tx.run(cast(LiteralString, query))
            except Exception as exc:
                logger.error("Failed to apply migration %s", migration_file.stem, exc_info=exc)
                return (index, migration_file.stem)

    return (len(migrations_to_apply), None)


def _generate_schema_diff(
    previous_schema: Dict[str, Any], current_schema: Dict[str, Any]
) -> List[str]:
    cypher_queries: List[str] = []

    # Only indexes/constraints from top level properties are taken into account
    previous_model_scheme_metadata: Optional[_ModelSchemaMetadata] = previous_schema.get("loomi")
    previous_props = previous_schema.get("properties", {})
    current_model_scheme_metadata: Optional[_ModelSchemaMetadata] = current_schema.get("loomi")
    current_props = current_schema.get("properties", {})

    if previous_model_scheme_metadata is None:
        raise MigrationError("Previous model schema metadata not found")

    if current_model_scheme_metadata is None:
        raise MigrationError("Current model schema metadata not found")

    previous_composite_indexes: _CompositeIndexesOrConstraints = {}
    current_composite_indexes: _CompositeIndexesOrConstraints = {}
    previous_composite_constraints: _CompositeIndexesOrConstraints = {}
    current_composite_constraints: _CompositeIndexesOrConstraints = {}

    previous_indexes: _IndexesOrConstraints = []
    current_indexes: _IndexesOrConstraints = []
    previous_constraints: _IndexesOrConstraints = []
    current_constraints: _IndexesOrConstraints = []

    props_to_check = set(previous_props.keys()).union(current_props.keys())
    for prop_name in props_to_check:
        previous_prop = previous_props.get(prop_name)
        current_prop = current_props.get(prop_name)

        if not previous_prop:
            # Property was newly added
            default_value = current_prop.get("default")
            if default_value:
                cypher_queries.append(
                    _generate_add_property_query(
                        current_model_scheme_metadata, prop_name, default_value
                    )
                )
        if not current_prop:
            # Property was removed
            cypher_queries.append(
                _generate_delete_property_query(current_model_scheme_metadata, prop_name)
            )

        if previous_prop:
            previous_prop_metadata: Dict[str, Any] = previous_prop.get("loomi", {})
            _get_index_or_constraint_definitions(
                previous_model_scheme_metadata,
                prop_name,
                previous_prop_metadata.get("indexes", []),
                previous_indexes,
                previous_composite_indexes,
            )
            _get_index_or_constraint_definitions(
                previous_model_scheme_metadata,
                prop_name,
                previous_prop_metadata.get("constraints", []),
                previous_constraints,
                previous_composite_constraints,
            )

        if current_prop:
            current_prop_metadata: Dict[str, Any] = current_prop.get("loomi", {})
            _get_index_or_constraint_definitions(
                current_model_scheme_metadata,
                prop_name,
                current_prop_metadata.get("indexes", []),
                current_indexes,
                current_composite_indexes,
            )
            _get_index_or_constraint_definitions(
                current_model_scheme_metadata,
                prop_name,
                current_prop_metadata.get("constraints", []),
                current_constraints,
                current_composite_constraints,
            )

    # create a hash from the indexes and constraints and check if any have been added/removed
    # should be able to use the same logic as for properties
    previous_definitions = _generate_index_or_constraint_hash(
        [
            *previous_indexes,
            *previous_constraints,
            *previous_composite_indexes.values(),
            *previous_composite_constraints.values(),
        ]
    )
    current_definitions = _generate_index_or_constraint_hash(
        [
            *current_indexes,
            *current_constraints,
            *current_composite_indexes.values(),
            *current_composite_constraints.values(),
        ]
    )

    hash_keys_to_check = set(previous_definitions.keys()) - set(current_definitions.keys())
    for hash_key in hash_keys_to_check:
        previous_definition = previous_definitions.get(hash_key)
        current_definition = current_definitions.get(hash_key)

        if not previous_definition:
            # Property was newly added
            default_value = current_definition.get("default")
            if default_value:
                cypher_queries.append(
                    _generate_add_property_query(
                        current_model_scheme_metadata, prop_name, default_value
                    )
                )
        if not current_definition:
            # Property was removed
            cypher_queries.append(
                _generate_delete_property_query(current_model_scheme_metadata, prop_name)
            )

    return []


def _get_index_or_constraint_definitions(
    model_schema_metadata: _ModelSchemaMetadata,
    prop_name: str,
    prop_indexes_or_constraints: List[_IndexOrConstraintMetadata],
    indexes_or_constraints: _IndexesOrConstraints,
    composite_indexes_or_constraints: _CompositeIndexesOrConstraints,
) -> None:
    for index_or_constraint_metadata in prop_indexes_or_constraints:
        if (
            model_schema_metadata.type == _JsonSchemaModelType.NODE
            and model_schema_metadata.labels
            and index_or_constraint_metadata.labels
        ):
            invalid_labels = index_or_constraint_metadata.labels - model_schema_metadata.labels

            if len(invalid_labels) != 0:
                raise MigrationError(
                    f"Invalid labels {', '.join(invalid_labels)} found. Only labels defined on the model "
                    "itself can be defined for indexes or constraints"
                )

        applied_labels_or_type: Set[str] = set()
        if model_schema_metadata.model_type == _JsonSchemaModelType.NODE:
            if index_or_constraint_metadata.labels:
                applied_labels_or_type.update(index_or_constraint_metadata.labels)
            else:
                applied_labels_or_type.update(cast(Set[str], model_schema_metadata.labels))
        else:
            applied_labels_or_type.add(model_schema_metadata.model_type)

        composite_key = index_or_constraint_metadata.composite_key
        if composite_key:
            composite_indexes_or_constraints.setdefault(
                composite_key,
                _IndexOrConstraintDefinition(
                    type=index_or_constraint_metadata.type,
                    name=index_or_constraint_metadata.name,
                    labels_or_type=applied_labels_or_type,
                    data_type=index_or_constraint_metadata.data_type,
                    properties=set([prop_name]),
                ),
            )

            if composite_key in composite_indexes_or_constraints:
                composite_name = composite_indexes_or_constraints[composite_key].name
                data_type = composite_indexes_or_constraints[composite_key].data_type

                if (
                    index_or_constraint_metadata.name is not None
                    and composite_name is not None
                    and index_or_constraint_metadata.name != composite_name
                ):
                    raise MigrationError(
                        "Index or constraint name can not be different for the same composite index or constraint"
                    )

                if (
                    index_or_constraint_metadata.data_type is not None
                    and data_type is not None
                    and index_or_constraint_metadata.data_type != data_type
                ):
                    raise MigrationError(
                        "Index or constraint data type can not be different for the same composite index or constraint"
                    )

                composite_indexes_or_constraints[composite_key].name = (
                    index_or_constraint_metadata.name
                )
                composite_indexes_or_constraints[composite_key].data_type = (
                    index_or_constraint_metadata.data_type
                )
                composite_indexes_or_constraints[composite_key].labels_or_type.update(
                    applied_labels_or_type
                )
                composite_indexes_or_constraints[composite_key].properties.add(prop_name)

            return

        indexes_or_constraints.append(
            _IndexOrConstraintDefinition(
                type=index_or_constraint_metadata.type,
                name=index_or_constraint_metadata.name,
                labels_or_type=applied_labels_or_type,
                data_type=index_or_constraint_metadata.data_type,
                properties=set([prop_name]),
            )
        )


def _generate_index_or_constraint_hash(
    definitions: List[_IndexOrConstraintDefinition],
) -> Dict[str, _IndexOrConstraintDefinition]:
    hashed: Dict[str, _IndexOrConstraintDefinition] = {}

    for definition in definitions:
        hash_key = xxhash.xxh64(definition.model_dump_json()).hexdigest()
        hashed[hash_key] = definition

    return hashed


def _generate_add_property_query(
    model_schema_metadata: _ModelSchemaMetadata, prop_name: str, default_value: Any
) -> str:
    set_value = str(default_value) if not isinstance(str, default_value) else f"'{default_value}'"

    model_type: Optional[_JsonSchemaModelType] = model_schema_metadata.model_type
    if model_type is None:
        raise MigrationError("Schema does not have a loomi.model_type property")

    if model_type == _JsonSchemaModelType.NODE:
        labels = model_schema_metadata.labels
        if labels is None:
            raise MigrationError("Node schema does not have a loomi.labels property")

        return f"MATCH (e:{':'.join(labels)}) SET e.{prop_name} = {set_value};"

    if model_type == _JsonSchemaModelType.RELATIONSHIP:
        type_ = model_schema_metadata.type
        if type_ is None:
            raise MigrationError("Relationship schema does not have a loomi.type property")

        return f"MATCH ()-[e:{type_}]->() SET e.{prop_name} = {set_value};"

    raise MigrationError(f"Unknown model_type {model_type} found")


def _generate_delete_property_query(
    model_schema_metadata: _ModelSchemaMetadata, prop_name: str
) -> str:
    model_type: Optional[_JsonSchemaModelType] = model_schema_metadata.model_type
    if model_type is None:
        raise MigrationError("Schema does not have a loomi.model_type property")

    if model_type == _JsonSchemaModelType.NODE:
        type_ = model_schema_metadata.labels
        if type_ is None:
            raise MigrationError("Node schema does not have a loomi.labels property")

        return f"MATCH (e:{':'.join(type_)}) REMOVE e.{prop_name};"

    if model_type == _JsonSchemaModelType.RELATIONSHIP:
        type_ = model_schema_metadata.type
        if type_ is None:
            raise MigrationError("Relationship schema does not have a loomi.type property")

        return f"MATCH ()-[e:{type_}]->() REMOVE e.{prop_name};"

    raise MigrationError(f"Unknown model_type {model_type} found")


def _generate_drop_index_or_constraint_query(definition: _IndexOrConstraintDefinition) -> str:
    if definition.type in (
        _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT,
        _JsonSchemaIndexOrConstraintType.EXISTENCE_CONSTRAINT,
        _JsonSchemaIndexOrConstraintType.DATA_TYPE_CONSTRAINT,
    ):
        return f"DROP CONSTRAINT {_get_index_or_constraint_name(False, definition.type, definition.labels_or_type, definition.properties)}"

    return f"DROP INDEX {_get_index_or_constraint_name(True, definition.type, definition.labels_or_type, definition.properties)}"


def _generate_create_index_or_constraint_query(
    model_schema_metadata: _ModelSchemaMetadata, definition: _IndexOrConstraintDefinition
) -> str:
    pattern = (
        f"(e:{':'.join(definition.labels_or_type)})"
        if model_schema_metadata.model_type == _JsonSchemaModelType.NODE
        else f"()-[e:{':'.join(definition.labels_or_type)}]-()"
    )

    match definition.type:
        case _JsonSchemaIndexOrConstraintType.UNIQUENESS_CONSTRAINT:
            if model_schema_metadata.model_type == _JsonSchemaModelType.NODE:
                return (
                    f"CREATE CONSTRAINT {_get_index_or_constraint_name(False, definition.type, definition.labels_or_type, definition.properties)}"
                    f"FOR {pattern}"
                    f"REQUIRE ({', '.join([f"e.{property_}" for property_ in definition.properties])}) IS UNIQUE"
                )


def _get_index_or_constraint_name(
    is_index: bool,
    type: _JsonSchemaIndexOrConstraintType,
    labels_or_type: Set[str],
    properties: Set[str],
) -> str:
    name_prefix = "ix" if is_index else "uq"
    return f"{name_prefix}_{type}_{'_'.join(labels_or_type)}_{'_'.join(properties)}"
