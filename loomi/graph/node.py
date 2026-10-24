import json
from typing import ClassVar, List, Set

from loomi._core.model_mixin import EntityConfiguration, ModelMixin
from loomi.exceptions import ModelError
from loomi.logger import get_logger

logger = get_logger("model")


class NodeConfiguration(EntityConfiguration, total=False):
    labels: Set[str]


class Node(ModelMixin):
    loomi_config: ClassVar[NodeConfiguration]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        cls.__merge_configs()
        super().__pydantic_init_subclass__(**kwargs)

        cls._hash = cls._generate_hash(list(cls.loomi_config["labels"]))  # type: ignore

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"element_id={self._element_id!r} "
            f"properties={self.__class__.model_fields!r} "
            f"labels={self.labels()!r}>"
        )

    @classmethod
    def labels(cls) -> Set[str]:
        labels = cls.loomi_config.get("labels")
        if labels is None:
            raise ModelError(
                f"Labels on model {cls.__name__} are not initialized. "
                f"Maybe you forgot to call {cls.model_rebuild.__name__}?"
            )

        return labels

    @classmethod
    def _generate_hash(cls, labels: List[str]) -> str:
        return f"n_{"_".join(sorted(labels))}"

    @classmethod
    def __merge_configs(cls) -> None:
        merged_config: NodeConfiguration = {
            "serializer_fn": json.dumps,
            "deserializer_fn": json.loads,
        }
        labels: Set[str] = set()

        for base in reversed(cls.__mro__):
            if not issubclass(base, Node) or base is Node:
                continue

            # Check if loomi_config is defined directly on this class
            if "loomi_config" in base.__dict__ and isinstance(base.__dict__["loomi_config"], dict):
                base_conf = base.__dict__["loomi_config"]

                # Handle labels merging
                if "labels" in base_conf:
                    parent_labels = base_conf["labels"]
                    if isinstance(parent_labels, set):
                        labels.update(parent_labels)
                    else:
                        logger.warning(
                            "Labels defined on parent class %s are not in the expected format. "
                            "Labels will be skipped",
                            base.__name__,
                        )

                # All other keys are either inherited if not defined or overwrite any defined value
                for key, val in base_conf.items():
                    if key != "labels":
                        merged_config[key] = val

            # If no labels are defined, fall back to the class name
            has_explicit_labels = (
                "loomi_config" in base.__dict__
                and isinstance(base.__dict__["loomi_config"], dict)
                and "labels" in base.__dict__["loomi_config"]
            )
            if not has_explicit_labels:
                labels.add(base.__name__)

        merged_config["labels"] = labels
        cls.loomi_config = merged_config
