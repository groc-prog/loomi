from typing import TYPE_CHECKING, Any, Union

from loomi._internal.types import NumericValue
from loomi.exceptions import QueryError
from loomi.query._templates import ArithmeticExpressionTemplate
from loomi.query.descriptors import FieldDescriptor
from loomi.query.expressions import Expression

if TYPE_CHECKING:
    from loomi.query.db_function import DbFunction
else:
    DbFunction = object


def add(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `+` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.ADD, value)


def reflected_add(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a reflected `+` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.R_ADD, value)


def subtract(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `-` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.SUBTRACT, value)


def reflected_subtract(
    property_descriptor: Any, value: Union[NumericValue, DbFunction]
) -> Expression:
    """
    Builds a reflected `-` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.R_SUBTRACT, value)


def multiply(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `*` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.MULTIPLY, value)


def reflected_multiply(
    property_descriptor: Any, value: Union[NumericValue, DbFunction]
) -> Expression:
    """
    Builds a reflected `*` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.R_MULTIPLY, value)


def divide(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `/` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.DIVIDE, value)


def reflected_divide(
    property_descriptor: Any, value: Union[NumericValue, DbFunction]
) -> Expression:
    """
    Builds a reflected `/` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.R_DIVIDE, value)


def modulo(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `%` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.MODULO, value)


def reflected_modulo(
    property_descriptor: Any, value: Union[NumericValue, DbFunction]
) -> Expression:
    """
    Builds a reflected `%` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.R_MODULO, value)


def pow_(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `^` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.POW, value)


def reflected_pow(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a reflected `^` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, (FieldDescriptor, DbFunction)):
        raise QueryError(
            f"Descriptor must be a valid field descriptor or db function. "
            f"Expected {FieldDescriptor.__name__} or {DbFunction.__name__}, got "
            f"{property_descriptor}"
        )

    return Expression(property_descriptor, ArithmeticExpressionTemplate.R_POW, value)
