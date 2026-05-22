from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Self,
    TypeVar,
    Union,
    overload,
)

from pydantic import BaseModel

from loomi._internal.types import ModelType
from loomi._logger import logger
from loomi.exceptions import QueryError
from loomi.query._context import CompilationContext
from loomi.query._protocols import CompilableExpression
from loomi.query.constants import OrderBy
from loomi.query.descriptors import FieldDescriptor

if TYPE_CHECKING:
    from loomi.graph.node import Node
    from loomi.graph.relationship import Relationship
else:
    Node = object
    Relationship = object

T = TypeVar("T", bound=Union[Node, Relationship, Dict[str, Any]])
P = TypeVar("P", bound=BaseModel)
R = TypeVar("R")


@dataclass
class _MatchQueryState:
    model_type: ModelType
    expressions: List[CompilableExpression] = field(default_factory=list)
    projection: Optional[Dict[str, Any]] = None
    order_by: Dict[str, Optional[OrderBy]] = field(default_factory=dict)
    limit: Optional[int] = None
    skip: Optional[int] = None


@dataclass
class MatchQueryBuilder(Generic[T, R]):
    """Query builder for fetching models using a loomi client."""

    _execute_fn: Callable[[str, Dict[str, Any]], R]
    _state: _MatchQueryState
    _compilation_ctx: CompilationContext

    def where(self, expression: Any) -> Self:
        """
        Adds filter expression for a WHERE clause.

        Args:
            expression (CompilableExpression): A expression which can be compiled by the query
            compiler.

        Raises:
            QueryError: If any invalid expression is provided.
        """
        if not isinstance(expression, CompilableExpression):
            raise QueryError(
                f"Invalid expression found. Expected {CompilableExpression.__name__}, "
                f"got {expression}"
            )

        self._state.expressions.append(expression)
        return self

    @overload
    def order_by(self, field_name: str, order: Optional[OrderBy] = None) -> Self: ...

    @overload
    def order_by(self, order: Dict[Any, OrderBy]) -> Self: ...

    @overload
    def order_by(self, descriptor: FieldDescriptor) -> Self: ...

    def order_by(  # type: ignore
        self,
        field_or_order: Union[str, Dict[Any, OrderBy], FieldDescriptor],
        order: Optional[OrderBy] = None,
    ) -> Self:
        """
        Adds one or multiple fields to order by.

        Args:
            field_or_order (Union[str, Dict[str, OrderBy]]): Either the field to order by or a
            dictionary with fields and their order.
            order (Optional[OrderBy]): The order to use. Only needed when defining a field as the
            first argument. Defaults to `None`

        Raises:
            QueryError: If a invalid field is provided.
        """
        order_by_map: Dict[str, Optional[OrderBy]] = {}

        if isinstance(field_or_order, str):
            order_by_map[field_or_order] = order
        elif isinstance(field_or_order, FieldDescriptor):
            field_name = field_or_order._full_path.rsplit(".", maxsplit=1)[-1]
            order_by_map[field_name] = order
        else:
            for field_name, order_by in field_or_order.items():
                if isinstance(field_name, FieldDescriptor):
                    order_by_map[field_name._full_path.rsplit(".", maxsplit=1)[-1]] = order_by
                else:
                    order_by_map[str(field_name)] = order_by

        for field_name, order_by in order_by_map.items():
            if field_name not in self._state.model_type.model_fields:
                raise QueryError(f"{field_name} is not a valid field to order by")

            if field_name in self._state.order_by:
                logger.warning(
                    "A order has already been defined for field %s. The old order will be "
                    "overwritten",
                    field_name,
                )

            self._state.order_by[field_name] = order_by

        return self

    def limit(self, limit: int) -> Self:
        """
        Adds a limit to the number of results returned by the query.

        Args:
            limit (int): The limit to apply.

        Raises:
            QueryError: If `limit` has a invalid value.
        """
        if limit < 0:
            raise QueryError("limit must be a positive integer if defined")

        if self._state.limit is not None:
            logger.warning(
                "A limit has already been defined for this query. The old limit will "
                "be overwritten"
            )

        self._state.limit = limit
        return self

    def skip(self, skip: int) -> Self:
        """
        Adds a skip to the number of results returned by the query.

        Args:
            skip (int): The skip to apply.

        Raises:
            QueryError: If `skip` has a invalid value.
        """
        if skip < 0:
            raise QueryError("skip must be a positive integer if defined")

        if self._state.skip is not None:
            logger.warning(
                "A skip has already been defined for this query. The old skip will "
                "be overwritten"
            )

        self._state.skip = skip
        return self

    def project(self, projection: Dict[str, Any]) -> "MatchQueryBuilder[Dict[str, Any], R]":
        """
        Adds a projection to apply to the returned data.

        Args:
            projection (Dict[str, Any]): The projection to apply.
        """
        if self._state.projection is not None:
            logger.warning(
                "A projection has already been defined for this query. The old projection will "
                "be overwritten"
            )

        self._state.projection = projection
        return MatchQueryBuilder(self._execute_fn, self._state, self._compilation_ctx)

    @overload
    def execute(self: "MatchQueryBuilder[T, Awaitable[Any]]") -> Awaitable[List[T]]: ...

    @overload
    def execute(self: "MatchQueryBuilder[T, List[Any]]") -> List[T]: ...

    def execute(self) -> Union[List[T], Awaitable[List[T]]]:
        """
        Runs the query. By default, a new session is created and used to run the query. You can
        optionally pass a transaction, which will be used instead.

        Returns:
            List[T]: A list of models.
        """
        from loomi.graph.node import Node

        model_variable = self._compilation_ctx.get_variable(self._state.model_type)

        query = ""
        if issubclass(self._state.model_type, Node):
            query = f"MATCH ({model_variable}:{':'.join(self._state.model_type._get_labels())})"
        else:
            query = f"MATCH ()-[{model_variable}:{self._state.model_type._get_type()}]->()"

        compiled_expressions = [
            expression._compile(self._compilation_ctx) for expression in self._state.expressions
        ]
        if len(compiled_expressions) != 0:
            query += f" WHERE {' AND '.join(compiled_expressions)}"

        if self._state.projection is not None:
            projected = [
                f"{model_variable}.{field_name} AS {projected_name}"
                for field_name, projected_name in self._state.projection.items()
            ]
            query += f" RETURN {', '.join(projected)}"
        else:
            query += f" RETURN {model_variable}"

        if self._state.order_by is not None and len(self._state.order_by.keys()) != 0:
            clauses: List[str] = []
            for field_name, order in self._state.order_by.items():
                clause = f"{model_variable}.{field_name}"

                if order is not None:
                    clause += f" {order.value}"

                clauses.append(clause)

            query += f" ORDER BY {', '.join(clauses)}"

        if self._state.skip is not None:
            query += f" SKIP {self._state.skip}"

        if self._state.limit is not None:
            query += f" LIMIT {self._state.limit}"

        return self._execute_fn(query, self._compilation_ctx.parameters)  # type: ignore
