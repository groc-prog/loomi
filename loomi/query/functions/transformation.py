from typing import Any

from loomi.query._templates import DbFunctionTemplate
from loomi.query.db_function import DbFunction


def tail(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `tail()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.TAIL, [])


def abs_(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `abs()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.ABS, [])


def ceil(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `ceil()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.CEIL, [])


def floor(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `floor()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.FLOOR, [])


def round_(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `round()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.ROUND, [])


def ltrim(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `ltrim()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.LTRIM, [])


def rtrim(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `rtrim()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.RTRIM, [])


def trim(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `trim()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.TRIM, [])


def to_lower(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `toLower()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.TO_LOWER, [])


def to_upper(property_descriptor: Any) -> DbFunction:
    """
    Wraps the descriptor or value in a `toUpper()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(property_descriptor, DbFunctionTemplate.TO_UPPER, [])
