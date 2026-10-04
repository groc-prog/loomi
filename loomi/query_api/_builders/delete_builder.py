from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Self,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from loomi._core.types import ModelType
from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import CompoundExpression
from loomi.query_api._core.protocols import CompilableExpression

if TYPE_CHECKING:
    from loomi.graph.relationship import Relationship
else:
    Relationship = object

R = TypeVar("R")


@dataclass(frozen=True)
class DeleteResult:
    """Result of a batch delete operation."""

    affected: int
    affected_ids: List[Tuple[str, int]]


@dataclass
class _DeleteQueryState:
    model_type: ModelType
    expressions: List[Union[CompoundExpression, CompilableExpression]] = field(default_factory=list)


@dataclass
class DeleteQueryBuilder(Generic[R]):
    """Query builder for batch deleting entities using a loomi client."""

    _execute_fn: Callable[[str, Dict[str, Any]], R]
    _state: _DeleteQueryState
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
        if not isinstance(expression, (CompoundExpression, CompilableExpression)):
            raise QueryError(
                f"Invalid expression found. Expected {CompilableExpression.__name__} "
                f"or {CompoundExpression.__name__}, got {expression}"
            )

        self._state.expressions.append(expression)
        return self

    def execute(self) -> R:
        """
        Runs the query. By default, a new session is created and used to run the query. You can
        optionally pass a transaction, which will be used instead.

        Returns:
            DeleteResult: The delete result.
        """
        from loomi.graph.node import Node

        model_variable = self._compilation_ctx.get_variable(self._state.model_type)
        is_node = issubclass(self._state.model_type, Node)

        query = ""
        if is_node:
            labels = ":".join(cast(Node, self._state.model_type)._get_labels())
            query = f"MATCH ({model_variable}:{labels})"
        else:
            type_ = cast(Relationship, self._state.model_type)._get_type()
            query = f"MATCH ()-[{model_variable}:{type_}]->()"

        query_strings = []
        for expression in self._state.expressions:
            if isinstance(expression, CompoundExpression):
                query_strings.append(expression.to_query_string(self._compilation_ctx))
            else:
                compiled_expression = expression._compile_expression(self._compilation_ctx)
                query_strings.append(compiled_expression.to_query_string())

        if len(query_strings) != 0:
            query += f" WHERE {' AND '.join(query_strings)}"

        if is_node:
            query += f" DETACH DELETE {model_variable}"
        else:
            query += f" DELETE {model_variable}"

        if self._compilation_ctx.server_type == ServerType.NEO4J:
            query += f" RETURN DISTINCT elementId({model_variable}), id({model_variable})"
        else:
            query += f" RETURN DISTINCT toString(id({model_variable})), id({model_variable})"

        return self._execute_fn(query, self._compilation_ctx.get_parameters())
