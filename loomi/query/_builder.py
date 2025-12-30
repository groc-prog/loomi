# pylint: disable=missing-function-docstring

import re
from dataclasses import dataclass
from typing import Any, Dict, List, LiteralString, Optional, Tuple, Union, cast

from loomi._logger import logger
from loomi.constants._graph import _ModelType
from loomi.exceptions import QueryCompileError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from loomi.query.helpers import _Predicate, _PredicateGroup

CompiledLoomiQuery = Tuple[LiteralString, Dict[str, Any]]


@dataclass
class _CompiledMatchPattern:
    pattern: str
    variable: str
    model: _ModelType


class _InternalQueryState:
    _node_variable_counter: int
    _relationship_variable_counter: int
    _parameter_variable_counter: int
    _iterator_variable_counter: int
    _alias_mapping: Dict[str, int]

    _match_patterns: List[_CompiledMatchPattern]
    _where_predicates: List[str]
    _set_clauses: List[str]
    _return_clauses: List[str]
    _parameters: Dict[str, Any]

    def __init__(self):
        self._match_patterns = []
        self._where_predicates = []
        self._set_clauses = []
        self._return_clauses = []
        self._parameters = {}
        self._node_variable_counter = 0
        self._relationship_variable_counter = 0
        self._parameter_variable_counter = 0
        self._iterator_variable_counter = 0
        self._alias_mapping = {}

    def add_match_pattern(self, model: _ModelType, alias: Optional[str]) -> None:
        if issubclass(model, LoomiNode):
            pattern = self._compile_node_pattern(model)
        elif issubclass(model, LoomiRelationship):
            pattern = self._compile_relationship_pattern(model)
        else:
            raise QueryCompileError("Model %s is not a valid Loomi model. Can not compile query")

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
        self._match_patterns.append(pattern)

        if alias:
            index = len(self._match_patterns) - 1
            self._alias_mapping[alias] = index

    def add_set_clause(self, property_name: str, value: Any, alias: Optional[str]) -> None:
        # TODO: add support for assigning values based on current db values
        compiled_match_pattern = self._resolve_compiled_match_pattern(alias)

        # The new value must pass validation for the field we try to set
        # Otherwise MATCH queries later on would fail validation
        model = compiled_match_pattern.model
        model.__pydantic_validator__.validate_assignment(
            model.model_construct(), property_name, value
        )

        self._set_clauses.append(
            f"{compiled_match_pattern.variable}.{property_name} = ${self._get_parameter(value)}"
        )

    def add_where_clause(self, predicate_or_group: Union[_PredicateGroup, _Predicate]) -> None:
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

    def add_return_clause(self, projection_alias: str, projection_expression: str) -> None:
        # Since a alias must be defined anyways for a projection to be available
        # we can validate the projected fields by splitting the express
        expression_parts = projection_expression.split(".", 1)
        alias = expression_parts[0]

        if alias not in self._alias_mapping:
            raise QueryCompileError(f"Alias {alias} is not bound to any pattern")

        pattern_index = self._alias_mapping[alias]
        compiled_pattern = self._match_patterns[pattern_index]

        # Only a variable has been defined in the projection, we do not need to validate
        # any fields
        if len(expression_parts) == 1:
            self._return_clauses.append(f"{compiled_pattern.variable} AS {projection_alias}")
            return

        # If a field has been defined in the projection, validate that it exists on the associated
        # model class
        # TODO: validate this better when nested fields are properly supported
        path = expression_parts[1]
        if path not in compiled_pattern.model.model_fields:
            raise QueryCompileError(
                (
                    f"Property {path} is not defined on model {compiled_pattern.model.__name__}. "
                    "If you intended to project the property on another model, use a alias to "
                    "reference it correctly"
                )
            )

        self._return_clauses.append(f"{projection_expression} AS {projection_alias}")

    def add_default_return_clauses(self) -> None:
        logger.debug("No projection defined, returning all variables from query")
        for compiled_pattern in self._match_patterns:
            self._return_clauses.append(compiled_pattern.variable)

    def compile(self) -> CompiledLoomiQuery:
        match_patterns = ", ".join(compiled.pattern for compiled in self._match_patterns)
        query = f"MATCH {match_patterns}"

        if len(self._where_predicates) != 0:
            where_clauses = " AND ".join(self._where_predicates)
            query = f"{query} WHERE {where_clauses}"

        if len(self._set_clauses) != 0:
            set_clauses = ", ".join(self._set_clauses)
            query = f"{query} SET {set_clauses}"

        if len(self._return_clauses) != 0:
            return_clauses = ", ".join(self._return_clauses)
            query = f"{query} RETURN {return_clauses}"

        return cast(LiteralString, query), self._parameters

    def _resolve_compiled_match_pattern(self, alias: Optional[str]) -> _CompiledMatchPattern:
        logger.debug("Resolving match pattern and")

        # Break here if no alias has been defined since we do not know which MATCH pattern the
        # property_name should belong to
        if len(self._match_patterns) > 1 and alias is None:
            raise QueryCompileError(
                (
                    "Cannot compile clause for multiple MATCH patterns without alias. "
                    "Define a alias for the pattern and reference it when calling this method"
                )
            )

        # If only one match pattern has been defined, we can say for sure that we use that one
        if alias is None:
            logger.debug("Using only added match pattern available")
            match_pattern = self._match_patterns[0]
        else:
            if alias not in self._alias_mapping:
                raise QueryCompileError(f"Alias {alias} is not bound to any pattern")

            logger.debug("Using match pattern for alias %s", alias)
            pattern_index = self._alias_mapping[alias]
            match_pattern = self._match_patterns[pattern_index]

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
            # The template_func uses predefined parameter names `p<index>` where index is the index
            # of the predicate from the predicates list
            template_func_ctx[f"p{index}"] = compiled_predicate

        return predicate_group.template_func(template_func_ctx)

    def _compile_predicate(self, predicate: _Predicate) -> str:
        logger.debug("Compiling predicate %s", predicate.predicate_type)
        compiled_match_pattern = self._resolve_compiled_match_pattern(predicate.alias)

        logger.debug("Building parameters for template function")
        template_func_ctx: Dict[str, Any] = {}
        for index, value in enumerate(predicate.values):
            # The template_func uses predefined parameter names `p<index>` where index is the index
            # of the value from the values tuple
            template_func_ctx[f"p{index}"] = self._get_parameter(value)

        logger.debug("Compiling provided property path")
        # This will result in groups like ["a.b.all_", "c.any_", "d"]
        path_segments = re.split(r"(?<=(?:all_|any_))\.", predicate.path)
        path_segments.reverse()

        # Map special path segments to their list predicates
        operators = {"all_": "ALL", "any_": "ANY"}
        expression = ""

        for index, segment in enumerate(path_segments):
            parts = segment.split(".")
            suffix = parts[-1]

            if suffix in operators:
                operator = operators[suffix]

                # If we are at the first segment (outer most) we need to prefix the path with the
                # variable, otherwise prefix it with the iterator which will be initialized in the
                # outer expression
                path_prefix = (
                    compiled_match_pattern.variable
                    if index == len(path_segments) - 1
                    else f"i{index}"
                )
                property_path = ".".join(parts[:-1])

                # The path is a list, which means the query should use the list item
                if index == len(path_segments) - 1:
                    iterator = f"i{index}" if len(path_segments) == 1 else f"i{index - 1}"

                    if len(path_segments) == 1:
                        predicate_expression = predicate.template_func(
                            {"path": iterator, **template_func_ctx}
                        )
                        expression = (
                            f"{operator}({iterator} IN {path_prefix}.{property_path} "
                            f"WHERE {predicate_expression})"
                        )
                    else:
                        expression = (
                            f"{operator}({iterator} IN {path_prefix}.{property_path} "
                            f"WHERE {expression})"
                        )
                else:
                    iterator = f"i{index}" if len(path_segments) == 1 else f"i{index - 1}"
                    expression = (
                        f"{operator}({iterator} IN {path_prefix}.{property_path} "
                        f"WHERE {expression})"
                    )
            else:
                # We are either at the last path segment or the only one
                path = (
                    f"{compiled_match_pattern.variable}.{segment}"
                    if len(path_segments) == 1
                    else f"i{index}.{segment}"
                )

                logger.debug("Compiling template function")
                expression = predicate.template_func({"path": path, **template_func_ctx})

        return expression

    def _get_parameter(self, value: Any) -> str:
        parameter_name = f"p{self._parameter_variable_counter}"
        self._parameter_variable_counter += 1

        logger.debug("Adding new parameter %s", parameter_name)
        self._parameters[parameter_name] = value
        return parameter_name

    def _compile_node_pattern(self, model: _ModelType) -> _CompiledMatchPattern:
        if "labels" not in model.loomi_config:
            raise QueryCompileError(f"Model {model.__name__} does not define any labels")

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
        return _CompiledMatchPattern(f"[{variable}:{model.loomi_config["type"]}]", variable, model)
