import json
import re
from typing import ClassVar

from loomi._core.model_mixin import EntityConfiguration, ModelMixin
from loomi.exceptions import ModelError


class RelationshipConfiguration(EntityConfiguration, total=False):
    """TypedDict for configuring Loomi relationship behavior."""

    type: str


class Relationship(ModelMixin):
    """A base class for Loomi relationships."""

    loomi_config: ClassVar[RelationshipConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        cls.__merge_configs()
        super().__pydantic_init_subclass__(**kwargs)

        cls._hash = cls._generate_hash(cls.loomi_config["type"])  # type: ignore

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} element_id={self._element_id!r} type={self._get_type()!r}>"
        )

    @classmethod
    def _get_normalized_type(cls) -> str:
        pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
        return pattern.sub("_", cls.__name__).upper()

    @classmethod
    def _generate_hash(cls, type_: str) -> str:
        return f"r_{type_}"

    @classmethod
    def _type_from_hash(cls, hash_: str) -> str:
        if not hash_.startswith("r_"):
            raise ModelError("Provided hash is not a relationship model hash")

        return hash_[2:]

    @classmethod
    def _get_type(cls) -> str:
        type_ = cls.loomi_config.get("type")
        if type_ is None:
            raise ModelError(
                f"Type on model {cls.__name__} is not initialized. Maybe "
                f"you forgot to call {cls.model_rebuild.__name__}?"
            )

        return type_

    @classmethod
    def __merge_configs(cls) -> None:
        merged_config: RelationshipConfiguration = {
            "serializer_fn": json.dumps,
            "deserializer_fn": json.loads,
        }

        for base in reversed(cls.__mro__):
            if not issubclass(base, Relationship) or base is Relationship:
                continue

            # Check if loomi_config is defined directly on this class
            if "loomi_config" in base.__dict__ and isinstance(base.__dict__["loomi_config"], dict):
                base_conf = base.__dict__["loomi_config"]

                # All other keys are either inherited if not defined or overwrite any defined value
                for key, val in base_conf.items():
                    merged_config[key] = val

            has_explicit_type = (
                "loomi_config" in base.__dict__
                and isinstance(base.__dict__["loomi_config"], dict)
                and "type" in base.__dict__["loomi_config"]
            )
            if not has_explicit_type:
                merged_config["type"] = cls._get_normalized_type()

        cls.loomi_config = merged_config
