from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Self, Tuple, TypeVar, Union, cast

from loomi._core.types import ModelType
from loomi._logger import logger
from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.descriptors import FieldDescriptor
from loomi.query_api._core.expressions import CompoundExpression
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableExpression,
    CompiledDbFunction,
)

R = TypeVar("R")


@dataclass(frozen=True)
class UpdateResult:
    """Result of a batch update operation."""

    affected: int
    affected_ids: List[Tuple[str, int]]


@dataclass
class _UpdateQueryState:
    model_type: ModelType
    filter_expressions: List[Union[CompoundExpression, CompilableExpression]] = field(
        default_factory=list
    )
    update_expressions: Dict[FieldDescriptor, Any] = field(default_factory=dict)


@dataclass
class UpdateQueryBuilder(Generic[R]):
    """Query builder for batch updating entities using a loomi client."""

    _execute_fn: Callable[[str, Dict[str, Any]], R]
    _state: _UpdateQueryState
    _compilation_ctx: CompilationContext

    def where(self, expression: Any) -> Self:
        """
        Adds filter expression for a WHERE clause.

        Args:
            expression (Union[CompoundExpression, CompilableExpression]): A expression which can be compiled by the
            query compiler.

        Raises:
            QueryError: If any invalid expression is provided.
        """
        if not isinstance(expression, CompilableExpression):
            raise QueryError(
                f"Invalid expression found. Expected {CompilableExpression.__name__}, "
                f"got {expression}"
            )

        self._state.filter_expressions.append(expression)
        return self

    def set_(self, model_field: Any, expression_or_value: Any) -> Self:
        """
        Adds filter expression for a WHERE clause.

        Args:
            expression (CompilableExpression): A expression which can be compiled by the query
            compiler.

        Raises:
            QueryError: If any invalid expression is provided.
        """
        if (
            not isinstance(model_field, FieldDescriptor)
            or model_field._model_type is not self._state.model_type
        ):
            raise QueryError(
                "Invalid field found. Expected a valid field of model "
                f"{self._state.model_type.__name__}, got {model_field._full_path}"
            )

        if model_field in self._state.update_expressions:
            logger.warning(
                "A set operation has already been defined for field %s. "
                "This will overwrite any operations defined prior to this one",
                model_field._full_path,
            )

        self._state.update_expressions[model_field] = expression_or_value
        return self

    def execute(self) -> R:
        """
        Runs the query. By default, a new session is created and used to run the query. You can
        optionally pass a transaction, which will be used instead.

        Returns:
            UpdateResult: The update result.
        """
        from loomi.graph.node import Node
        from loomi.graph.relationship import Relationship

        if len(self._state.update_expressions.keys()) == 0:
            raise QueryError("At least one update expression must be defined")

        model_variable = self._compilation_ctx.get_variable(self._state.model_type)
        is_node = issubclass(self._state.model_type, Node)

        query = ""
        if is_node:
            labels = ":".join(cast(Node, self._state.model_type)._get_labels())
            query = f"MATCH ({model_variable}:{labels})"
        else:
            type_ = cast(Relationship, self._state.model_type)._get_type()
            query = f"MATCH ()-[{model_variable}:{type_}]->()"

        filter_query_strings = []
        for expression in self._state.filter_expressions:
            if isinstance(expression, CompoundExpression):
                filter_query_strings.append(expression.to_query_string(self._compilation_ctx))
            else:
                compiled_expression = expression._compile_expression(self._compilation_ctx)
                filter_query_strings.append(compiled_expression.to_query_string())

        if len(filter_query_strings) != 0:
            query += f" WHERE {' AND '.join(filter_query_strings)}"

        set_query_strings: List[str] = []
        for model_field, expression_or_value in self._state.update_expressions.items():
            value_assignment: str

            if isinstance(expression_or_value, CompilableDbFunction):
                compiled = expression_or_value._compile_db_function(self._compilation_ctx)

                if isinstance(compiled, CompiledDbFunction):
                    value_assignment = compiled.to_query_string()
                else:
                    value_assignment = compiled.variable_path.format(variable=compiled.variable)
            elif isinstance(expression_or_value, CompilableExpression):
                compiled = expression_or_value._compile_expression(self._compilation_ctx)
                value_assignment = compiled.to_query_string()
            else:
                parameter = self._compilation_ctx.add_parameter(expression_or_value)
                value_assignment = f"${parameter}"

            set_query_strings.append(
                f"{model_variable}.{model_field._full_path} = {value_assignment}"
            )

        query += f" SET {', '.join(set_query_strings)}"

        if self._compilation_ctx.server_type == ServerType.NEO4J:
            query += f" RETURN DISTINCT elementId({model_variable}), id({model_variable})"
        else:
            query += f" RETURN DISTINCT toString(id({model_variable})), id({model_variable})"

        return self._execute_fn(query, self._compilation_ctx.get_parameters())
