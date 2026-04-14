import re
from typing import ClassVar

from loomi._internal.base_model import EntityBase, EntityConfiguration
from loomi.exceptions import ModelError


class RelationshipConfiguration(EntityConfiguration, total=False):
    """TypedDict for configuring Loomi relationship behavior."""

    type: str


class Relationship(EntityBase):
    """A base class for Loomi relationships."""

    loomi_config: ClassVar[RelationshipConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)

        if not hasattr(cls, "loomi_config"):
            setattr(cls, "loomi_config", RelationshipConfiguration())

        if "type" not in cls.loomi_config:
            cls.loomi_config["type"] = cls._get_normalized_type()

        for parent in cls.__mro__[1:]:
            if not hasattr(parent, "loomi_config"):
                continue

            inherited_config = getattr(parent, "loomi_config", None)
            if inherited_config is None:
                raise ModelError(
                    f"Parent class {parent.__name__} has no `loomi_config` attribute. Maybe you "
                    f"forgot to call {cls.model_rebuild.__name__}?"
                )

            cls._merge_config(inherited_config)

        cls._init_config_defaults()
        cls._hash = cls._generate_hash(cls.loomi_config["type"])

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} element_id={self._element_id!r} type={self._get_type()!r}>"
        )

    @classmethod
    def _merge_config(cls, config: RelationshipConfiguration) -> None:
        for key, value in config.items():
            # We can not merge the type here and we do not want duplicate types, so
            # we skip
            if key == "type":
                continue

            if key not in cls.loomi_config:
                cls.loomi_config[key] = value

    @classmethod
    def _get_normalized_type(cls) -> str:
        pattern = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
        return pattern.sub("_", cls.__name__).upper()

    @classmethod
    def _generate_hash(cls, type_: str) -> str:
        return f"r_{type_}"

    @classmethod
    def _get_type(cls) -> str:
        type_ = cls.loomi_config.get("type")
        if type_ is None:
            raise ModelError(
                f"Type on model {cls.__name__} is not initialized. Maybe "
                f"you forgot to call {cls.model_rebuild.__name__}?"
            )

        return type_
