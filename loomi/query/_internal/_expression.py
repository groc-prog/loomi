# pylint: disable=missing-function-docstring

import abc
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi.exceptions import QueryError
from loomi.query._internal._types import _QueryModelType

if TYPE_CHECKING:
    from loomi.query._internal._property_descriptor import _PropertyDescriptor
else:
    _PropertyDescriptor = object


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
    _variable_counter = 0
    _models_to_vars: Dict[_QueryModelType, str]
    parameters: Dict[str, Any]

    def __init__(self) -> None:
        self._variable_counter = 0
        self._models_to_vars = {}
        self.parameters = {}

    def add_parameter(self, value: Any) -> str:
        parameter_name = f"p{len(self.parameters.keys())}"
        self.parameters[parameter_name] = value

        return parameter_name

    def get_variable(self, model: _QueryModelType) -> str:
        if model not in self._models_to_vars:
            raise QueryError(f"Model {model.__name__} is not known in the current query context")

        return self._models_to_vars[model]

    def register_model(self, model: _QueryModelType) -> None:
        from loomi.query.helpers import AliasedModel

        variable = model._alias if isinstance(model, AliasedModel) else f"v{self._variable_counter}"
        if variable in set(self._models_to_vars.values()):
            raise QueryError(
                f"Variable {variable} has already been defined. If you are using a aliased model "
                ", make sure it's alias is unique"
            )

        self._variable_counter = self._variable_counter + 1
        self._models_to_vars[model] = variable


@dataclass
class _BaseQueryExpression:
    @abc.abstractmethod
    def _compile(self, ctx: "_ExpressionContext") -> str:
        pass

    def __invert__(self) -> "CompoundQueryExpression":
        from loomi.query.helpers import not_

        return not_(self)

    def __and__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        return CompoundQueryExpression(_LogicalExpressionOperator.AND, [self, other])

    def __or__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        return CompoundQueryExpression(_LogicalExpressionOperator.OR, [self, other])

    def __xor__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        return CompoundQueryExpression(_LogicalExpressionOperator.XOR, [self, other])


@dataclass
class QueryExpression(_BaseQueryExpression):
    """A expression which can be compiled by a query builder."""

    property_descriptor: _PropertyDescriptor
    template: _ExpressionTemplate
    value: Any

    def _compile(self, ctx: _ExpressionContext) -> str:
        return self.property_descriptor._compile_path(ctx, self.template.value, self.value)


@dataclass
class UnaryQueryExpression(_BaseQueryExpression):
    """A unary expression which can be compiled by a query builder."""

    property_descriptor: _PropertyDescriptor
    template: _UnaryExpressionTemplate

    def _compile(self, ctx: _ExpressionContext) -> str:
        return self.property_descriptor._compile_path(ctx, self.template.value, None)


@dataclass
class CompoundQueryExpression:
    """A compound expression which can be compiled by a query builder."""

    operator: _LogicalExpressionOperator
    expressions: List[Union["CompoundQueryExpression", _BaseQueryExpression]]

    def __and__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        if self.operator == _LogicalExpressionOperator.AND:
            return CompoundQueryExpression(
                _LogicalExpressionOperator.AND, [*self.expressions, other]
            )

        return CompoundQueryExpression(_LogicalExpressionOperator.AND, [self, other])

    def __or__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        if self.operator == _LogicalExpressionOperator.OR:
            return CompoundQueryExpression(
                _LogicalExpressionOperator.OR, [*self.expressions, other]
            )

        return CompoundQueryExpression(_LogicalExpressionOperator.OR, [self, other])

    def __xor__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        if self.operator == _LogicalExpressionOperator.XOR:
            return CompoundQueryExpression(
                _LogicalExpressionOperator.XOR, [*self.expressions, other]
            )

        return CompoundQueryExpression(_LogicalExpressionOperator.XOR, [self, other])

    def __invert__(self) -> "CompoundQueryExpression":
        from loomi.query.helpers import not_

        return not_(self)

    def _compile(self, ctx: _ExpressionContext) -> str:
        compiled: List[str] = []
        for expression in self.expressions:
            if isinstance(expression, CompoundQueryExpression):
                compiled.append(f"({expression._compile(ctx)})")
            else:
                compiled.append(expression._compile(ctx))

        return f" {self.operator.value} ".join(compiled)
