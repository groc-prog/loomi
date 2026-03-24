# pylint: disable=missing-function-docstring

from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi._internal._types import QueryModelType
from loomi._logger import logger
from loomi.constants import ServerType
from loomi.exceptions import QueryError

if TYPE_CHECKING:
    from loomi.query.descriptor import _Descriptor
else:
    _Descriptor = object


class _ExpressionTemplate(StrEnum):
    EQ = "{variable} = {parameter}"
    NEQ = "{variable} <> {parameter}"
    GT = "{variable} > {parameter}"
    GTE = "{variable} >= {parameter}"
    LT = "{variable} < {parameter}"
    LTE = "{variable} <= {parameter}"
    IN = "{variable} IN {parameter}"
    STARTS_WITH = "{variable} STARTS WITH {parameter}"
    ENDS_WITH = "{variable} ENDS WITH {parameter}"
    CONTAINS = "{variable} CONTAINS {parameter}"
    REGEX = "{variable} =~ {parameter}"


class _UnaryExpressionTemplate(StrEnum):
    IS_NULL = "{variable} IS NULL"
    IS_NOT_NULL = "{variable} IS NOT NULL"


class _LogicalExpressionOperator(StrEnum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"


class _ExpressionContext:
    _server_type: ServerType
    _variable_counter = 0
    _models_to_vars: Dict[QueryModelType, str]
    _parameters: Dict[str, Any]

    def __init__(self, server_type: ServerType) -> None:
        self._server_type = server_type
        self._variable_counter = 0
        self._models_to_vars = {}
        self._parameters = {}

    def force_increment_variable_counter(self, amount: int = 1) -> None:
        self._variable_counter = self._variable_counter + amount

    def add_parameter(self, value: Any) -> str:
        logger.debug("Adding new parameter to expression context")
        parameter_name = f"p{len(self._parameters.keys())}"
        self._parameters[parameter_name] = value

        return parameter_name

    def get_variable(self, model: QueryModelType) -> str:
        if model not in self._models_to_vars:
            raise QueryError(f"Model {model.__name__} is not known in the current query context")

        return self._models_to_vars[model]

    def add_model(self, model: QueryModelType) -> None:
        from loomi.query.functions import AliasedModel

        logger.debug(
            "Registering %s with expression context",
            (f"alias {model._alias}" if isinstance(model, AliasedModel) else model.__name__),
        )

        variable = model._alias if isinstance(model, AliasedModel) else f"v{self._variable_counter}"
        if variable in set(self._models_to_vars.values()):
            raise QueryError(
                f"Variable {variable} has already been defined. If you are using a aliased model "
                ", make sure it's alias is unique"
            )

        self._variable_counter = self._variable_counter + 1
        self._models_to_vars[model] = variable


@dataclass(frozen=True)
class _BaseQueryExpression:
    @abstractmethod
    def _compile(self, ctx: "_ExpressionContext") -> str: ...

    def __invert__(self) -> "InvertQueryExpression":
        from loomi.query.functions import not_

        return not_(self)

    def __and__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        from loomi.query.functions import and_

        return and_(self, other)

    def __or__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        from loomi.query.functions import or_

        return or_(self, other)

    def __xor__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        from loomi.query.functions import xor

        return xor(self, other)


@dataclass(frozen=True)
class QueryExpression(_BaseQueryExpression):
    """A expression which can be compiled by a query builder."""

    property_descriptor: _Descriptor
    template: _ExpressionTemplate
    value: Any

    def _compile(self, ctx: _ExpressionContext) -> str:
        return self.property_descriptor._compile_path(ctx, self.template.value, self.value)


@dataclass(frozen=True)
class NullQueryExpression(_BaseQueryExpression):
    """A null-check expression which can be compiled by a query builder."""

    property_descriptor: _Descriptor
    template: _UnaryExpressionTemplate

    def _compile(self, ctx: _ExpressionContext) -> str:
        return self.property_descriptor._compile_path(ctx, self.template.value, None)


@dataclass(frozen=True)
class InvertQueryExpression(_BaseQueryExpression):
    """A invert expression which can be compiled by a query builder."""

    expression: Union["CompoundQueryExpression", _BaseQueryExpression]

    def _compile(self, ctx: _ExpressionContext) -> str:
        compiled = self.expression._compile(ctx)
        return f"NOT({compiled})"


@dataclass(frozen=True)
class CompoundQueryExpression:
    """A compound expression which can be compiled by a query builder."""

    operator: _LogicalExpressionOperator
    expressions: List[Union["CompoundQueryExpression", _BaseQueryExpression]]

    def __and__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions import and_

        if self.operator == _LogicalExpressionOperator.AND:
            return and_(*self.expressions, other)

        return and_(self, other)

    def __or__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions import or_

        if self.operator == _LogicalExpressionOperator.OR:
            return or_(*self.expressions, other)

        return or_(self, other)

    def __xor__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions import xor

        if self.operator == _LogicalExpressionOperator.XOR:
            return xor(*self.expressions, other)

        return xor(self, other)

    def __invert__(self) -> "InvertQueryExpression":
        from loomi.query.functions import not_

        return not_(self)

    def _compile(self, ctx: _ExpressionContext) -> str:
        compiled: List[str] = []
        for expression in self.expressions:
            if isinstance(expression, CompoundQueryExpression):
                compiled.append(f"({expression._compile(ctx)})")
            else:
                compiled.append(expression._compile(ctx))

        return f" {self.operator.value} ".join(compiled)


@dataclass(frozen=True)
class CustomQueryExpression(_BaseQueryExpression):
    """
    A expression containing custom Cypher query parts which can be compiled by the
    query builder.
    """

    expression_template: str
    template_references: Dict[str, QueryModelType]
    parameter_references: Dict[str, Any]

    def _compile(self, ctx: _ExpressionContext) -> str:
        from loomi.graph.node import Node
        from loomi.graph.relationship import Relationship
        from loomi.query.functions import AliasedModel

        resolved_template_references: Dict[str, Any] = {}
        for key, model in self.template_references.items():
            if isinstance(model, AliasedModel):
                variable = ctx.get_variable(model)
                resolved_template_references[key] = variable
                continue

            if issubclass(model, (Node, Relationship)):
                variable = ctx.get_variable(model)
                resolved_template_references[key] = variable
                continue

            raise QueryError(
                "Template references must be valid models or aliased models. "
                f"Got {model} for reference {key}"
            )

        resolved_parameter_references: Dict[str, Any] = {}
        for key, value in self.parameter_references.items():
            parameter = ctx.add_parameter(value)
            resolved_template_references[key] = parameter

        return self.expression_template.format(
            **resolved_template_references, **resolved_parameter_references
        )
