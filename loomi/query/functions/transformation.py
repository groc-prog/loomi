from typing import Any

from loomi.exceptions import QueryError
from loomi.query._templates import DbFunctionTemplate
from loomi.query.descriptor import FieldDescriptor
from loomi.query.transformers import DbFunctionTransformer


def tail(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `tail()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.TAIL)


def abs_(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `abs()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.ABS)


def ceil(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `ceil()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.CEIL)


def floor(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `floor()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.FLOOR)


def round_(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `round()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.ROUND)


def ltrim(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `ltrim()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.LTRIM)


def rtrim(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `rtrim()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.RTRIM)


def trim(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `trim()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.TRIM)


def to_lower(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `toLower()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.TO_LOWER)


def to_upper(property_descriptor: Any) -> DbFunctionTransformer:
    """
    Wraps the descriptor or value in a `toUpper()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionTransformer: A transformer which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return DbFunctionTransformer(property_descriptor, DbFunctionTemplate.TO_UPPER)
