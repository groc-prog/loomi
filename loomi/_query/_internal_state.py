from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from loomi._logger import logger
from loomi.clients.async_client import LoomiAsyncClient
from loomi.clients.sync_client import LoomiClient
from loomi.constants._graph import _ModelType
from loomi.exceptions import QueryCompileError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship


@dataclass
class _MatchPattern:
    pattern: str
    variable: str
    model: _ModelType


class _InternalQueryState:
    _client: Union[LoomiClient, LoomiAsyncClient]

    _node_variable_counter: int
    _relationship_variable_counter: int
    _parameter_variable_counter: int

    _match_patterns: Dict[Union[_ModelType, str], _MatchPattern]
    _where_predicates: List[str]
    _set_clauses: List[str]
    _parameters: Dict[str, Any]

    def __init__(self, client: Union[LoomiClient, LoomiAsyncClient]):
        self._client = client
        self._match_patterns = {}
        self._where_predicates = []
        self._set_clauses = []
        self._parameters = {}
        self._node_variable_counter = 0
        self._relationship_variable_counter = 0
        self._parameter_variable_counter = 0

    def add_match_pattern(self, model: _ModelType, alias: Optional[str]) -> None:
        """
        Adds a new match pattern to the state based on the provided model.

        Args:
            model: (Union[Type[LoomiNode], Type[LoomiRelationship]]): The model type to compile a
            pattern from.
            alias (Optional[str]): Alias for referencing variable later..
        """
        if issubclass(model, LoomiNode):
            pattern = self._compile_node_pattern(model)
        elif issubclass(model, LoomiRelationship):
            pattern = self._compile_relationship_pattern(model)
        else:
            raise QueryCompileError(
                "Model %s is not a valid Loomi model. Can not compile query"
            )

        if len(self._match_patterns) != 0 and alias is None:
            logger.warning(
                (
                    "Adding multiple MATCH patterns to query without defining a alias. This could "
                    "prevent the query from compiling successfully"
                )
            )

        key = alias or model
        self._match_patterns[key] = pattern

    def add_set_clause(self, property_: str, value: Any, alias: Optional[str]) -> None:
        """
        Adds a new set clause to the state based on the provided alias. If no alias is defined and
        only one match pattern exists, it is used.

        Args:
            property_ (str): The property to set.
            value (Any): The value to set.
            alias (Optional[str]): Alias of the match pattern to be used in the set clause. Required
            if more than 1 match pattern has been defined

        Raises:
            QueryCompileError: If no alias is defined but multiple match patterns exist.
            QueryCompileError: If the provided alias does not match any pattern.
        """
        if len(self._match_patterns) > 1 and alias is None:
            raise QueryCompileError(
                (
                    "Cannot compile SET clause for multiple MATCH patterns without alias. "
                    "Define a alias for the pattern and reference it when calling this method"
                )
            )

        if alias is None:
            match_pattern = next(iter(self._match_patterns.values()))
        else:
            if alias not in self._match_patterns:
                raise QueryCompileError(f"Alias {alias} is not bound to any pattern")
            match_pattern = self._match_patterns[alias]

        model_fields = match_pattern.model.model_fields
        if property_ not in model_fields:
            raise QueryCompileError(
                (
                    f"Property {property_} is not defined on model {match_pattern.model.__name__}. "
                    "If you intended to set the property on another model, use a alias to "
                    "reference it"
                )
            )

        annotation = model_fields[property_].annotation
        if annotation and not isinstance(value, annotation):
            raise QueryCompileError(
                (
                    f"Annotation of property {property_} on model {match_pattern.model.__name__} "
                    f"does not match provided value {value}."
                )
            )

        self._set_clauses.append(
            f"{match_pattern.variable}.{property_} = ${self._compile_parameter(value)}"
        )

    def compile_and_run(self) -> None:
        print("DONE")

    def _compile_parameter(self, value: Any) -> str:
        parameter_name = f"p{self._parameter_variable_counter}"
        self._parameter_variable_counter += 1

        self._parameters[parameter_name] = value
        return parameter_name

    def _compile_node_pattern(self, model: _ModelType) -> _MatchPattern:
        if "labels" not in model.loomi_config:
            raise QueryCompileError(
                f"Model {model.__name__} does not define any labels"
            )

        labels = ":".join(model.loomi_config["labels"])
        variable = f"n{self._node_variable_counter}"
        self._node_variable_counter += 1

        logger.debug(
            "Compiling match pattern for model %s with variable %s",
            model.__name__,
            variable,
        )
        return _MatchPattern(f"({variable}:{labels})", variable, model)

    def _compile_relationship_pattern(self, model: _ModelType) -> _MatchPattern:
        if "type" not in model.loomi_config:
            raise QueryCompileError(f"Model {model.__name__} does not define a type")

        variable = f"n{self._relationship_variable_counter}"
        self._relationship_variable_counter += 1

        logger.debug(
            "Compiling match pattern for model %s with variable %s",
            model.__name__,
            variable,
        )
        return _MatchPattern(
            f"[{variable}:{model.loomi_config["type"]}]", variable, model
        )
