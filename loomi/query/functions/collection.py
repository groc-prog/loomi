from typing import Any, List, TypeVar, Union, cast, get_args, get_origin

P = TypeVar("P")


def all_(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `ALL` when a query builder encounters it.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    from loomi.query.descriptor import FieldDescriptor, ListPathOperator

    descriptor = cast(FieldDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{descriptor._full_path}.{ListPathOperator.ALL.value}",
            inferred_type,
            descriptor._model_type,
        ),
    )


def any_(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `ANY` when a query builder encounters it. This is also
    the default which will be used if nothing is defined for a list property.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    from loomi.query.descriptor import FieldDescriptor, ListPathOperator

    descriptor = cast(FieldDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{descriptor._full_path}.{ListPathOperator.ANY.value}",
            inferred_type,
            descriptor._model_type,
        ),
    )


def none(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `NONE` when a query builder encounters it.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    from loomi.query.descriptor import FieldDescriptor, ListPathOperator

    descriptor = cast(FieldDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{descriptor._full_path}.{ListPathOperator.NONE.value}",
            inferred_type,
            descriptor._model_type,
        ),
    )


def single(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `SINGLE` when a query builder encounters it.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    from loomi.query.descriptor import FieldDescriptor, ListPathOperator

    descriptor = cast(FieldDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        FieldDescriptor(
            f"{descriptor._full_path}.{ListPathOperator.SINGLE.value}",
            inferred_type,
            descriptor._model_type,
        ),
    )
