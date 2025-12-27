import hashlib
import re
from typing import ClassVar

from loomi.exceptions import ModelInitializationError
from loomi.models._base import LoomiBaseConfiguration, _LoomiBase


class LoomiRelationshipConfiguration(LoomiBaseConfiguration, total=False):
    """TypedDict for configuring Loomi relationship behavior."""

    type: str


class LoomiRelationship(_LoomiBase):
    """A base class for creating Loomi relationship models."""

    loomi_config: ClassVar[LoomiRelationshipConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)

        if not hasattr(cls, "loomi_config"):
            setattr(cls, "loomi_config", LoomiRelationshipConfiguration())

        if "type" not in cls.loomi_config:
            cls.loomi_config["type"] = cls.__get_normalized_type()

        for parent in cls.__mro__[1:]:
            if not hasattr(parent, "loomi_config"):
                continue

            inherited_config = getattr(parent, "loomi_config", None)
            if not inherited_config:
                raise ModelInitializationError(
                    f"Parent class {parent.__name__} has no `loomi_config` attribute"
                )

            cls.__merge_loomi_config(inherited_config)

        cls._hash = cls._generate_loomi_hash(cls.loomi_config["type"])

    @classmethod
    def __merge_loomi_config(cls, config: LoomiRelationshipConfiguration) -> None:
        for key, value in config.items():
            # We can not merge the type here and we do not want duplicate types, so
            # we skip
            if key == "type":
                continue
            # If the key has not been set before, always set it
            if key not in cls.loomi_config:
                cls.loomi_config[key] = value

    @classmethod
    def __get_normalized_type(cls) -> str:
        pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
        return pattern.sub("_", cls.__name__).upper()

    @classmethod
    def _generate_loomi_hash(cls, type_: str) -> str:
        normalized = f"r_{type_}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
