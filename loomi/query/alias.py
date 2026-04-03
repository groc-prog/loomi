import re
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from loomi._internal._types import ModelType
from loomi.exceptions import ModelError

T = TypeVar("T", bound=ModelType)


@dataclass(frozen=True)
class AliasedModel:
    """
    Model proxy allowing the same model type to be referenced multiple times with different
    variable names in queries.
    """

    _alias: str
    _model_type: ModelType

    def __getattribute__(self, name: str) -> Any:
        from loomi.query.descriptors import FieldDescriptor

        if name.startswith("_"):
            return super().__getattribute__(name)

        if name in self._model_type.model_fields:
            return FieldDescriptor(
                name, cast(Any, self._model_type.model_fields[name].annotation), self
            )

        raise ModelError("Aliased models only expose field descriptors")


def create_alias(model_type: T, alias: str) -> T:
    """
    Creates a new `AliasedModel` instance which can be used to reference the same model type
    multiple times under different variables in the same query.

    Args:
        model_type: (ModelType): The model to create a alias for.
        alias (str): The alias which will be used in queries. Can be any string which does
        **not match** the format **v<any number>**.

    Raises:
        ModelError: If attempting to use the reserved format for the alias.

    Returns:
        AliasedModel: The model which can be used in queries.
    """
    if re.match(r"^v\d+", alias):
        raise ModelError("Aliases with a pattern 'v<number>' are reserved for internal use")

    return cast(T, AliasedModel(alias, model_type))
