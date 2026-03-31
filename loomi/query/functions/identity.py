from loomi._internal._types import QueryModelType
from loomi.query._templates import EntityIdExpressionTemplate
from loomi.query.descriptor import EntityIdDescriptor


def element_id(model_type: QueryModelType) -> EntityIdDescriptor:
    """
    Builds a descriptor which will be resolved to an `elementId` expression when used by a
    query builder.

    Args:
        model_type: (QueryModelType): The model to create a `elementId` expression for.

    Returns:
        EntityIdDescriptor: A entity id expression which can be used by a query builder.
    """
    return EntityIdDescriptor(model_type, EntityIdExpressionTemplate.ELEMENT_ID)


def id_(model_type: QueryModelType) -> EntityIdDescriptor:
    """
    Builds a descriptor which will be resolved to an `id` expression when used by a
    query builder.

    Args:
        model_type: (QueryModelType): The model to create a `id` expression for.

    Returns:
        EntityIdDescriptor: A entity id expression which can be used by a query builder.
    """
    return EntityIdDescriptor(model_type, EntityIdExpressionTemplate.ID)
