from typing import Any

from loomi.query._templates import DbFunctionTemplate
from loomi.query.descriptor import DbFunctionDescriptor


def to_lower(property_descriptor: Any) -> DbFunctionDescriptor:
    """
    Wraps the descriptor or value in a `toLower()` function.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to wrap.

    Returns:
        DbFunctionDescriptor: A descriptor which can be compiled by a query builder.
    """
    return DbFunctionDescriptor(property_descriptor, DbFunctionTemplate.TO_LOWER)
