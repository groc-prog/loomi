from typing import Any, Dict, List, Union

from loomi._core.types import NumericValue, QueryModelType
from loomi.exceptions import QueryError
from loomi.query_api._core.expressions import (
    CompoundExpression,
    CustomCypherExpression,
    Expression,
    InvertExpression,
)
from loomi.query_api._core.protocols import (
    CompilableAndRunnableExpression,
    CompilableDbFunction,
    CompilableDescriptor,
)
from loomi.query_api._core.templates import ExpressionTemplate, LogicalExpressionTemplate


def equals(to_wrap: Any, value: Any) -> CompilableAndRunnableExpression:
    """
    Builds a `=` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (Any): The value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.EQ, value)


def not_equals(to_wrap: Any, value: Any) -> CompilableAndRunnableExpression:
    """
    Builds a `<>` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (Any): The value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.NEQ, value)


def greater_than(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `>` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.GT, value)


def greater_than_or_equal(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `>=` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.GTE, value)


def less_than(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `<` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.LT, value)


def less_than_or_equal(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `<=` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.LTE, value)


def not_(
    expression: Union[CompoundExpression, CompilableAndRunnableExpression],
) -> CompilableAndRunnableExpression:
    """
    Builds a `NOT(...)` expression for a query builder.

    Args:
        expression (Union[CompoundExpression, _BaseExpression]): The expression
        to invert.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    return InvertExpression(expression)


def and_(
    *expressions: Union[CompoundExpression, CompilableAndRunnableExpression],
) -> CompoundExpression:
    """
    Builds a `AND(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, _BaseExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    return CompoundExpression(LogicalExpressionTemplate.AND, [*expressions])


def or_(
    *expressions: Union[CompoundExpression, CompilableAndRunnableExpression],
) -> CompoundExpression:
    """
    Builds a `OR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, _BaseExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    return CompoundExpression(LogicalExpressionTemplate.OR, [*expressions])


def xor(
    *expressions: Union[CompoundExpression, CompilableAndRunnableExpression],
) -> CompoundExpression:
    """
    Builds a `XOR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, _BaseExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    return CompoundExpression(LogicalExpressionTemplate.XOR, [*expressions])


def is_null(to_wrap: Any) -> CompilableAndRunnableExpression:
    """
    Builds a `IS NULL` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, CompilableDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {CompilableDescriptor.__name__} "
            f", got {to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.IS_NULL, None)


def is_not_null(to_wrap: Any) -> CompilableAndRunnableExpression:
    """
    Builds a `IS NOT NULL` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, CompilableDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {CompilableDescriptor.__name__} "
            f", got {to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.IS_NOT_NULL, None)


def in_(
    to_wrap: Any, value: Union[List[Any], CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `IN` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (List[Any]): The (list) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.IN, value)


def starts_with(
    to_wrap: Any, value: Union[str, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `STARTS WITH` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (str): The (string) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.STARTS_WITH, value)


def ends_with(
    to_wrap: Any, value: Union[str, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `ENDS WITH` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (str): The (string) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.ENDS_WITH, value)


def contains(
    to_wrap: Any, value: Union[str, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `CONTAINS` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (str): The (string) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.CONTAINS, value)


def regex(to_wrap: Any, value: Union[str, CompilableDbFunction]) -> CompilableAndRunnableExpression:
    """
    Builds a `=~` expression for a query builder.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.
        value (str): The (string) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(to_wrap, (CompilableDescriptor, CompilableDbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {CompilableDescriptor.__name__} or {CompilableDbFunction.__name__}, got "
            f"{to_wrap}"
        )

    return Expression(to_wrap, ExpressionTemplate.REGEX, value)


def cypher(
    template: str, model_map: Dict[str, QueryModelType], parameter_map: Dict[str, Any]
) -> CompilableAndRunnableExpression:
    """
    Builds a special query expression which can contain custom Cypher expressions. The resulting
    expression can contain any valid Cypher expressions.

    [!NOTE] Parameter placeholders **must not** include the `$` prefix

    Args:
        template (str): The custom expression used as a template.
        model_map (Dict[str, QueryModelType]): A map of template placeholders and their
        corresponding models. At compile time, the placeholders will be replaced with their actual
        variable names.
        parameter_map (Dict[str, Any]): A map of template placeholders and their corresponding
        parameter values. At compile time, the placeholders will be replaced with their actual
        parameter names.

    Returns:
        CompilableAndRunnableExpression: A expression which can be compiled by a query builder.
    """
    return CustomCypherExpression(template, model_map, parameter_map)
