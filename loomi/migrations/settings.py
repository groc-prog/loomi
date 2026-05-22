# pylint: disable=too-many-arguments, too-many-positional-arguments, missing-function-docstring

from pathlib import Path
from typing import Optional, Set, Tuple, Type

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)

from loomi.constants import ServerType


class MigrationSettings(BaseSettings):
    """Settings for customizing how migrations behave."""

    db_dsn: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DB_DSN", "db_dsn"),
    )
    server_type: Optional[ServerType] = Field(
        default=None,
        validation_alias=AliasChoices("SERVER_TYPE", "server_type"),
    )
    models_dir: Path = Field(
        default=Path("./models"),
        validation_alias=AliasChoices("MODELS_DIR", "models_dir"),
    )
    migration_dir: Path = Field(
        default=Path("./migrations"),
        validation_alias=AliasChoices("MIGRATIONS_DIR", "migration_dir"),
    )
    migration_node_labels: Set[str] = Field(
        default={"__Migration__"},
        validation_alias=AliasChoices("MIGRATION_NODE_LABELS", "migration_node_labels"),
    )
    migration_relationship_type: str = Field(
        default="__APPLIED__BEFORE__",
        validation_alias=AliasChoices("MIGRATION_RELATIONSHIP_TYPE", "migration_relationship_type"),
    )

    @field_validator("migration_dir", "models_dir", mode="after")
    @classmethod
    def resolve_and_validate_path(cls, v: Path) -> Path:
        resolved = v.resolve()

        if not resolved.exists():
            resolved.mkdir(parents=True, exist_ok=True)

        if not resolved.is_dir():
            raise ValueError(f"The path '{resolved}' exists but is not a directory.")

        return resolved

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, PyprojectTomlConfigSettingsSource(settings_cls))

    model_config = SettingsConfigDict(
        env_prefix="LOOMI_", pyproject_toml_table_header=("tool", "loomi"), extra="ignore"
    )
