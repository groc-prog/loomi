# pylint: disable=missing-function-docstring

from typing import Any, Dict, List, Union

from loomi.exceptions import ModelInitializationError, QueryError
from loomi.models._internal._types import _ModelType
from loomi.models.node import LoomiNode
from loomi.queries.alias import LoomiQueryAlias


class _InternalBuilderState:
    variable_map: Dict[str, str]
    match_patterns: List[str]
    parameters: Dict[str, Any] = {}

    def __init__(self):
        self.variable_map = {}
        self.match_patterns = []
        self.parameters = {}

    def get_parameter(self) -> str:
        return f"p_{len(self.parameters)}"

    def get_existing_or_new_variable(
        self, model_type_or_alias: Union[_ModelType, LoomiQueryAlias]
    ) -> str:
        hash_ = model_type_or_alias._hash
        if hash_ is None:
            model_name = (
                model_type_or_alias._model_type.__name__
                if isinstance(model_type_or_alias, LoomiQueryAlias)
                else model_type_or_alias.__name__
            )
            raise ModelInitializationError(
                f"Model {model_name} not fully initialized. Expected type to be defined"
            )

        variable_name = self.variable_map.get(hash_)
        if variable_name is not None:
            return variable_name

        if isinstance(model_type_or_alias, LoomiQueryAlias):
            variable_name = model_type_or_alias._alias
        else:
            char = "n" if issubclass(model_type_or_alias, LoomiNode) else "r"
            variable_name = f"{char}_{len(self.variable_map)}"

        if variable_name in self.variable_map:
            raise QueryError(
                f"Alias {variable_name} has already been defined. Use another alias or let the "
                "builder auto generate a variable name"
            )

        self.variable_map[hash_] = variable_name
        return variable_name
