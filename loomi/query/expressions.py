# pylint: disable=missing-function-docstring

from dataclasses import dataclass
from typing import Any, Dict, List, Union

from loomi._internal._types import QueryModelType
from loomi.exceptions import QueryError
from loomi.query._context import ExpressionContext
from loomi.query._protocols import CompilableDescriptor, CompilableExpression
from loomi.query._templates import (
    ExpressionTemplate,
    LogicalExpressionOperator,
    UnaryExpressionTemplate,
)
from loomi.query.alias import AliasedModel


@dataclass(frozen=True)
class _BaseQueryExpression(CompilableExpression):
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

    property_descriptor: CompilableDescriptor
    template: ExpressionTemplate
    value: Any

    def _compile(self, ctx: ExpressionContext) -> str:
        return self.property_descriptor._compile(ctx, self.template.value, self.value)


@dataclass(frozen=True)
class NullQueryExpression(_BaseQueryExpression):
    """A null-check expression which can be compiled by a query builder."""

    property_descriptor: CompilableDescriptor
    template: UnaryExpressionTemplate

    def _compile(self, ctx: ExpressionContext) -> str:
        return self.property_descriptor._compile(ctx, self.template.value, None)


@dataclass(frozen=True)
class InvertQueryExpression(_BaseQueryExpression):
    """A invert expression which can be compiled by a query builder."""

    expression: Union["CompoundQueryExpression", _BaseQueryExpression]

    def _compile(self, ctx: ExpressionContext) -> str:
        compiled = self.expression._compile(ctx)
        return f"NOT({compiled})"


@dataclass(frozen=True)
class CompoundQueryExpression:
    """A compound expression which can be compiled by a query builder."""

    operator: LogicalExpressionOperator
    expressions: List[Union["CompoundQueryExpression", _BaseQueryExpression]]

    def __and__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions import and_

        if self.operator == LogicalExpressionOperator.AND:
            return and_(*self.expressions, other)

        return and_(self, other)

    def __or__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions import or_

        if self.operator == LogicalExpressionOperator.OR:
            return or_(*self.expressions, other)

        return or_(self, other)

    def __xor__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions import xor

        if self.operator == LogicalExpressionOperator.XOR:
            return xor(*self.expressions, other)

        return xor(self, other)

    def __invert__(self) -> "InvertQueryExpression":
        from loomi.query.functions import not_

        return not_(self)

    def _compile(self, ctx: ExpressionContext) -> str:
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

    def _compile(self, ctx: ExpressionContext) -> str:
        from loomi.graph.node import Node
        from loomi.graph.relationship import Relationship

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
