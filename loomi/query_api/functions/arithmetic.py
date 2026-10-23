from typing import Any

from loomi.exceptions import QueryError
from loomi.query_api._core.expressions import Expression
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableDescriptor,
    CompilableExpression,
)
from loomi.query_api._core.templates import ArithmeticExpressionTemplate


def _validate_wrapped_value(value: Any) -> None:
    if not isinstance(
        value, (int, float, CompilableDescriptor, CompilableDbFunction, CompilableExpression)
    ):
        raise QueryError("Value must be a valid compilable or numeric value")


def _validate_value(value: Any) -> None:
    if not isinstance(
        value, (int, float, CompilableDescriptor, CompilableDbFunction, CompilableExpression)
    ):
        raise QueryError("Value must be a valid compilable or numeric value")

    field_descriptor_fn = getattr(value, "_is_list_path", None)
    if field_descriptor_fn is not None and field_descriptor_fn():
        raise QueryError("Field descriptor with list path operators are not allowed as values")


def add(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `+` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.ADD, value)


def reflected_add(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a reflected `+` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_ADD, value)


def subtract(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `-` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.SUBTRACT, value)


def reflected_subtract(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a reflected `-` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_SUBTRACT, value)


def multiply(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `*` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.MULTIPLY, value)


def reflected_multiply(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a reflected `*` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_MULTIPLY, value)


def divide(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `/` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.DIVIDE, value)


def reflected_divide(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a reflected `/` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_DIVIDE, value)


def modulo(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `%` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.MODULO, value)


def reflected_modulo(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a reflected `%` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_MODULO, value)


def pow_(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `^` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.POW, value)


def reflected_pow(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a reflected `^` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided value or value to wrap is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap)
    _validate_value(value)

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_POW, value)
