import re
from typing import ClassVar, TypedDict

from loomi._core.model_mixin import ModelMixin
from loomi.exceptions import ModelError


class RelationshipConfiguration(TypedDict, total=False):
    type: str


class Relationship(ModelMixin):
    loomi_config: ClassVar[RelationshipConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        cls.__merge_configs()
        super().__pydantic_init_subclass__(**kwargs)

        cls._hash = cls._generate_hash(cls.loomi_config["type"])  # type: ignore

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"element_id={self._element_id!r} "
            f"properties={self.__class__.model_fields!r} "
            f"labels={self.type()!r}>"
        )

    @classmethod
    def type(cls) -> str:
        type_ = cls.loomi_config.get("type")
        if type_ is None:
            raise ModelError(
                f"Type on model {cls.__name__} is not initialized. Maybe "
                f"you forgot to call {cls.model_rebuild.__name__}?"
            )

        return type_

    @classmethod
    def _generate_hash(cls, type_: str) -> str:
        return f"r_{type_}"

    @classmethod
    def __merge_configs(cls) -> None:
        merged_config: RelationshipConfiguration = {}

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
                merged_config["type"] = cls.__get_normalized_type()

        cls.loomi_config = merged_config

    @classmethod
    def __get_normalized_type(cls) -> str:
        pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
        return pattern.sub("_", cls.__name__).upper()
