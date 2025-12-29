# pylint: disable=missing-function-docstring

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from loomi._logger import logger
from loomi.clients.async_client import LoomiAsyncClient
from loomi.clients.sync_client import LoomiClient
from loomi.constants._graph import _ModelType
from loomi.exceptions import QueryCompileError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from loomi.query.filters import _Predicate, _PredicateGroup


@dataclass
class _CompiledMatchPattern:
    pattern: str
    variable: str
    model: _ModelType


class _InternalQueryState:
    _client: Union[LoomiClient, LoomiAsyncClient]

    _node_variable_counter: int
    _relationship_variable_counter: int
    _parameter_variable_counter: int

    _match_patterns: Dict[Union[_ModelType, str], _CompiledMatchPattern]
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

        logger.debug(
            "Adding new pattern %s %s",
            pattern,
            "with alias" if alias else "without alias",
        )
        key = alias or model
        self._match_patterns[key] = pattern

    def add_set_clause(
        self, property_name: str, value: Any, alias: Optional[str]
    ) -> None:
        compiled_match_pattern = self._resolve_compiled_match_pattern(
            property_name, alias
        )

        annotation = compiled_match_pattern.model.model_fields[property_name].annotation
        if annotation and not isinstance(value, annotation):
            raise QueryCompileError(
                (
                    f"Annotation of property {property_name} on model "
                    f"{compiled_match_pattern.model.__name__} does not match provided value "
                    f"{value}."
                )
            )

        self._set_clauses.append(
            f"{compiled_match_pattern.variable}.{property_name} = ${self._compile_parameter(value)}"
        )

    def add_where_clause(
        self, predicate_or_group: Union[_PredicateGroup, _Predicate]
    ) -> None:
        if isinstance(predicate_or_group, _PredicateGroup):
            compiled = self._compile_predicate_group(predicate_or_group)
        elif isinstance(predicate_or_group, _Predicate):
            compiled = self._compile_predicate(predicate_or_group)
        else:
            raise QueryCompileError(
                "Encountered unknown class while compiling predicates. Expected one of "
                f"{_Predicate.__name__} or {_PredicateGroup.__name__}, but found "
                f"{predicate_or_group}"
            )

        self._where_predicates.append(compiled)

    def compile_and_run(self) -> None:
        print("DONE")

    def _resolve_compiled_match_pattern(
        self, property_name: str, alias: Optional[str]
    ) -> _CompiledMatchPattern:
        logger.debug(
            "Resolving match pattern and validating existence of property %s",
            property_name,
        )
        if len(self._match_patterns) > 1 and alias is None:
            raise QueryCompileError(
                (
                    "Cannot compile clause for multiple MATCH patterns without alias. "
                    "Define a alias for the pattern and reference it when calling this method"
                )
            )

        if alias is None:
            logger.debug("Using only added match pattern available")
            match_pattern = next(iter(self._match_patterns.values()))
        else:
            if alias not in self._match_patterns:
                raise QueryCompileError(f"Alias {alias} is not bound to any pattern")

            logger.debug("Using match pattern for alias %s", alias)
            match_pattern = self._match_patterns[alias]

        model_fields = match_pattern.model.model_fields
        if property_name not in model_fields:
            raise QueryCompileError(
                (
                    f"Property {property_name} is not defined on model "
                    "{match_pattern.model.__name__}. If you intended to set the property on "
                    "another model, use a alias to reference it"
                )
            )

        return match_pattern

    def _compile_predicate_group(self, predicate_group: _PredicateGroup) -> str:
        logger.debug("Compiling predicate group %s", predicate_group.group_type)
        compiled_predicates: List[str] = []

        for predicate_or_group in predicate_group.predicates:
            if isinstance(predicate_or_group, _PredicateGroup):
                compiled = self._compile_predicate_group(predicate_or_group)
            elif isinstance(predicate_or_group, _Predicate):
                compiled = self._compile_predicate(predicate_or_group)
            else:
                raise QueryCompileError(
                    "Encountered unknown class while compiling predicates. Expected one of "
                    f"{_Predicate.__name__} or {_PredicateGroup.__name__}, but found "
                    f"{predicate_or_group}"
                )

            compiled_predicates.append(compiled)

        template_func_ctx: Dict[str, Any] = {}
        for index, compiled_predicate in enumerate(compiled_predicates):
            template_func_ctx[f"p{index}"] = compiled_predicate

        return predicate_group.template_func(template_func_ctx)

    def _compile_predicate(self, predicate: _Predicate) -> str:
        logger.debug("Compiling predicate %s", predicate.predicate_type)
        compiled_match_pattern = self._resolve_compiled_match_pattern(
            predicate.property_name, predicate.alias
        )

        logger.debug("Building parameters for template function")
        template_func_ctx: Dict[str, Any] = {}
        for index, value in enumerate(predicate.values):
            template_func_ctx[f"p{index}"] = self._compile_parameter(value)

        logger.debug("Compiling template function")
        return predicate.template_func(
            {
                "variable": compiled_match_pattern.variable,
                "property": predicate.property_name,
                **template_func_ctx,
            }
        )

    def _compile_parameter(self, value: Any) -> str:
        parameter_name = f"p{self._parameter_variable_counter}"
        self._parameter_variable_counter += 1

        logger.debug("Adding new parameter %s", parameter_name)
        self._parameters[parameter_name] = value
        return parameter_name

    def _compile_node_pattern(self, model: _ModelType) -> _CompiledMatchPattern:
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
        return _CompiledMatchPattern(f"({variable}:{labels})", variable, model)

    def _compile_relationship_pattern(self, model: _ModelType) -> _CompiledMatchPattern:
        if "type" not in model.loomi_config:
            raise QueryCompileError(f"Model {model.__name__} does not define a type")

        variable = f"n{self._relationship_variable_counter}"
        self._relationship_variable_counter += 1

        logger.debug(
            "Compiling match pattern for model %s with variable %s",
            model.__name__,
            variable,
        )
        return _CompiledMatchPattern(
            f"[{variable}:{model.loomi_config["type"]}]", variable, model
        )
