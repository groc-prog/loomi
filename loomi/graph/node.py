from typing import ClassVar, List, Set, cast

from loomi._internal._base_model import _EntityBase, _EntityConfiguration
from loomi.exceptions import ModelError


class NodeConfiguration(_EntityConfiguration, total=False):
    """TypedDict for configuring Loomi node behavior."""

    labels: Set[str]


class Node(_EntityBase):
    """A base class for Loomi nodes."""

    loomi_config: ClassVar[NodeConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)

        if not hasattr(cls, "loomi_config"):
            setattr(cls, "loomi_config", NodeConfiguration())

        # If not labels have been defined, fall back to the class name
        if "labels" not in cls.loomi_config:
            cls.loomi_config["labels"] = {cls.__name__}

        for parent in cls.__mro__[1:]:
            if not hasattr(parent, "loomi_config"):
                continue

            inherited_config = getattr(parent, "loomi_config", None)
            if not inherited_config:
                raise ModelError(
                    f"Parent class {parent.__name__} has no `loomi_config` attribute. Maybe you "
                    f"forgot to call {cls.model_rebuild.__name__}?"
                )

            cls._merge_config(inherited_config)

        cls._init_config_defaults()
        cls._hash = cls._generate_hash(list(cls.loomi_config["labels"]))

    def __repr__(self) -> str:
        labels = self.loomi_config.get("labels", set())
        return f"<{self.__class__.__name__} element_id={self._element_id!r} labels={labels!r}>"

    @classmethod
    def _merge_config(cls, config: NodeConfiguration) -> None:
        for key, value in config.items():
            if key not in cls.loomi_config:
                cls.loomi_config[key] = value

            # If the key is a set (we are dealing with labels), merge them
            if isinstance(value, set):
                cls.loomi_config[key] = cast(Set[str], cls.loomi_config[key]).union(value)

    @classmethod
    def _generate_hash(cls, labels: List[str]) -> str:
        return f"n_{"_".join(sorted(labels))}"
