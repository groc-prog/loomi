import hashlib
import json
import re
from typing import ClassVar

from loomi.models.base import LoomiBaseConfiguration, _LoomiBase


class LoomiRelationshipConfiguration(LoomiBaseConfiguration, total=False):
    """TypedDict for configuring Loomi relationship behavior."""

    type: str


class LoomiRelationship(_LoomiBase):
    """A base class for creating Loomi relationship models."""

    loomi_config: ClassVar[LoomiRelationshipConfiguration] = (
        LoomiRelationshipConfiguration()
    )

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)

        if not hasattr(cls, "loomi_config"):
            setattr(cls, "loomi_config", LoomiRelationshipConfiguration())

        for parent in cls.__mro__[1:]:
            if not hasattr(parent, "loomi_config"):
                continue

            inherited_config = getattr(parent, "loomi_config", None)
            if not inherited_config:
                continue

            cls.__merge_loomi_config(inherited_config)

        if "type" not in cls.loomi_config or cls.loomi_config["type"] is None:
            cls.loomi_config["type"] = cls.__get_normalized_type()

        cls._hash = cls._generate_loomi_hash(cls.loomi_config["type"])

    @classmethod
    def __merge_loomi_config(cls, config: LoomiRelationshipConfiguration) -> None:
        for key, value in config.items():
            # If the key has not been set before, always set it
            if key not in cls.loomi_config:
                cls.loomi_config[key] = value
            # If the type has been inherited, we need to update it to the normalized name of
            # the current class
            elif (
                key == "type"
                and "type" in cls.loomi_config
                and value == cls.loomi_config["type"]
            ):
                cls.loomi_config["type"] = cls.__get_normalized_type()

    @classmethod
    def __get_normalized_type(cls) -> str:
        pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
        return pattern.sub("_", cls.__name__).upper()

    @classmethod
    def _generate_loomi_hash(cls, type_: str) -> str:
        return hashlib.sha256(json.dumps([type_]).encode("utf-8")).hexdigest()
