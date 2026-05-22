from typing import Any, List, TypeVar, Union, cast, get_args, get_origin

from loomi.exceptions import QueryError
from loomi.query.descriptors import FieldDescriptor, ListPathOperator

P = TypeVar("P")


def all_(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `ALL` when a query builder encounters it.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    current_type = property_descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if not isinstance(a, type(None))), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{property_descriptor._full_path}.{ListPathOperator.ALL.value}",
            inferred_type,
            property_descriptor._model_type,
        ),
    )


def any_(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `ANY` when a query builder encounters it. This is also
    the default which will be used if nothing is defined for a list property.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    current_type = property_descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if not isinstance(a, type(None))), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{property_descriptor._full_path}.{ListPathOperator.ANY.value}",
            inferred_type,
            property_descriptor._model_type,
        ),
    )


def none(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `NONE` when a query builder encounters it.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    current_type = property_descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if not isinstance(a, type(None))), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{property_descriptor._full_path}.{ListPathOperator.NONE.value}",
            inferred_type,
            property_descriptor._model_type,
        ),
    )


def single(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `SINGLE` when a query builder encounters it.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    current_type = property_descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if not isinstance(a, type(None))), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{property_descriptor._full_path}.{ListPathOperator.SINGLE.value}",
            inferred_type,
            property_descriptor._model_type,
        ),
    )
