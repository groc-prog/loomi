import hashlib
import re
from typing import ClassVar, TypedDict

from loomi.exceptions import ModelInitializationError
from loomi.models._internal._base import _LoomiBase


class LoomiRelationshipConfiguration(TypedDict, total=False):
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
            cls.loomi_config["type"] = cls._get_normalized_type()

        for parent in cls.__mro__[1:]:
            if not hasattr(parent, "loomi_config"):
                continue

            inherited_config = getattr(parent, "loomi_config", None)
            if not inherited_config:
                raise ModelInitializationError(
                    f"Parent class {parent.__name__} has no `loomi_config` attribute"
                )

        cls._hash = cls._generate_loomi_hash(cls.loomi_config["type"])

    @classmethod
    def _get_normalized_type(cls) -> str:
        pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
        return pattern.sub("_", cls.__name__).upper()

    @classmethod
    def _generate_loomi_hash(cls, type_: str) -> str:
        normalized = f"r_{type_}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
