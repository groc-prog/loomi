from typing import Any, Union

from loomi._core.types import NumericValue
from loomi.exceptions import QueryError
from loomi.query_api._core.expressions import Expression
from loomi.query_api._core.protocols import (
    CompilableAndRunnableExpression,
    CompilableDbFunction,
    CompilableDescriptor,
)
from loomi.query_api._core.templates import ArithmeticExpressionTemplate


def add(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `+` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.ADD, value)


def reflected_add(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a reflected `+` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_ADD, value)


def subtract(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `-` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.SUBTRACT, value)


def reflected_subtract(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a reflected `-` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_SUBTRACT, value)


def multiply(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `*` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.MULTIPLY, value)


def reflected_multiply(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a reflected `*` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_MULTIPLY, value)


def divide(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `/` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.DIVIDE, value)


def reflected_divide(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a reflected `/` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_DIVIDE, value)


def modulo(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `%` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.MODULO, value)


def reflected_modulo(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a reflected `%` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_MODULO, value)


def pow_(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a `^` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.POW, value)


def reflected_pow(
    to_wrap: Any, value: Union[NumericValue, CompilableDbFunction]
) -> CompilableAndRunnableExpression:
    """
    Builds a reflected `^` expression for a query builder.

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

    return Expression(to_wrap, ArithmeticExpressionTemplate.R_POW, value)
