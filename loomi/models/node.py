from typing import ClassVar, List, Set, cast

from loomi.exceptions import ModelError
from loomi.models._internal._base import _EntityBase, _EntityConfiguration


class LoomiNodeConfiguration(_EntityConfiguration, total=False):
    """TypedDict for configuring Loomi node behavior."""

    labels: Set[str]


class LoomiNode(_EntityBase):
    """A base class for creating Loomi node models."""

    loomi_config: ClassVar[LoomiNodeConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)

        if not hasattr(cls, "loomi_config"):
            setattr(cls, "loomi_config", LoomiNodeConfiguration())
            cls._init_config_defaults()

        # If not labels have been defined, fall back to the class name
        if "labels" not in cls.loomi_config:
            cls.loomi_config["labels"] = {cls.__name__}

        for parent in cls.__mro__[1:]:
            if not hasattr(parent, "loomi_config"):
                continue

            inherited_config = getattr(parent, "loomi_config", None)
            if not inherited_config:
                raise ModelError(f"Parent class {parent.__name__} has no `loomi_config` attribute")

            cls._merge_loomi_config(inherited_config)

        cls._hash = cls._generate_loomi_hash(list(cls.loomi_config["labels"]))

    def __repr__(self) -> str:
        labels = self.loomi_config.get("labels", set())
        return f"<{self.__class__.__name__} element_id={self._element_id!r} labels={labels!r}>"

    @classmethod
    def _merge_loomi_config(cls, config: LoomiNodeConfiguration) -> None:
        for key, value in config.items():
            # If the key has not been set before, always set it
            if key not in cls.loomi_config:
                cls.loomi_config[key] = value

            # If the key is a set (we are dealing with labels), merge them
            if isinstance(value, set):
                cls.loomi_config[key] = cast(Set[str], cls.loomi_config[key]).union(value)

    @classmethod
    def _generate_loomi_hash(cls, labels: List[str]) -> str:
        return f"n_{"_".join(sorted(labels))}"
