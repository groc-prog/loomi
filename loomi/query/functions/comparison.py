from typing import Any, List, Union

from loomi._internal._types import NumericValue
from loomi.exceptions import QueryError
from loomi.query._templates import (
    ExpressionTemplate,
    LogicalExpressionOperator,
    UnaryExpressionTemplate,
)
from loomi.query.expressions import (
    CompoundQueryExpression,
    InvertQueryExpression,
    NullQueryExpression,
    QueryExpression,
    _BaseQueryExpression,
)


def equals(property_descriptor: Any, value: Any) -> QueryExpression:
    """
    Builds a `=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Any): The value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    return QueryExpression(property_descriptor, ExpressionTemplate.EQ, value)


def not_equals(property_descriptor: Any, value: Any) -> QueryExpression:
    """
    Builds a `<>` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Any): The value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    return QueryExpression(property_descriptor, ExpressionTemplate.NEQ, value)


def greater_than(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `>` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {ExpressionTemplate.GT.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.GT, value)


def greater_than_or_equal(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `>=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {ExpressionTemplate.GTE.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.GTE, value)


def less_than(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `<` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {ExpressionTemplate.LT.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.LT, value)


def less_than_or_equal(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `<=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {ExpressionTemplate.LTE.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.LTE, value)


def not_(
    expression: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> InvertQueryExpression:
    """
    Builds a `NOT(...)` expression for a query builder.

    Args:
        expression (Union[CompoundQueryExpression, _BaseQueryExpression]): The expression
        to invert.

    Returns:
        InvertQueryExpression: A expression which can be compiled by a query builder.
    """
    return InvertQueryExpression(expression)


def and_(
    *expressions: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> CompoundQueryExpression:
    """
    Builds a `AND(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundQueryExpression, _BaseQueryExpression]): The expressions
        to join.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(LogicalExpressionOperator.AND, [*expressions])


def or_(
    *expressions: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> CompoundQueryExpression:
    """
    Builds a `OR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundQueryExpression, _BaseQueryExpression]): The expressions
        to join.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(LogicalExpressionOperator.OR, [*expressions])


def xor(
    *expressions: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> CompoundQueryExpression:
    """
    Builds a `XOR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundQueryExpression, _BaseQueryExpression]): The expressions
        to join.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(LogicalExpressionOperator.XOR, [*expressions])


def is_null(property_descriptor: Any) -> NullQueryExpression:
    """
    Builds a `IS NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    return NullQueryExpression(
        property_descriptor,
        UnaryExpressionTemplate.IS_NULL,
    )


def is_not_null(property_descriptor: Any) -> NullQueryExpression:
    """
    Builds a `IS NOT NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    return NullQueryExpression(
        property_descriptor,
        UnaryExpressionTemplate.IS_NOT_NULL,
    )


def in_(property_descriptor: Any, value: List[Any]) -> QueryExpression:
    """
    Builds a `IN` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (List[Any]): The (list) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, list):
        raise QueryError(f"Values for {ExpressionTemplate.IN.name} expressions must be valid lists")

    return QueryExpression(property_descriptor, ExpressionTemplate.IN, value)


def starts_with(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `STARTS WITH` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, str):
        raise QueryError(
            f"Values for {ExpressionTemplate.STARTS_WITH.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.STARTS_WITH, value)


def ends_with(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `ENDS WITH` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, str):
        raise QueryError(
            f"Values for {ExpressionTemplate.ENDS_WITH.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.ENDS_WITH, value)


def contains(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `CONTAINS` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, str):
        raise QueryError(
            f"Values for {ExpressionTemplate.CONTAINS.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.CONTAINS, value)


def regex(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `=~` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(value, str):
        raise QueryError(
            f"Values for {ExpressionTemplate.REGEX.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, ExpressionTemplate.REGEX, value)
