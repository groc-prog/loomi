import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, TypeVar, Union, cast, get_args, get_origin

from loomi._internal._types import ModelType, NumericValue, QueryModelType
from loomi.constants import ServerType
from loomi.exceptions import ModelError, QueryError
from loomi.query.expressions import (
    CompoundQueryExpression,
    CustomQueryExpression,
    InvertQueryExpression,
    NullQueryExpression,
    QueryExpression,
    _BaseQueryExpression,
    _ExpressionTemplate,
    _LogicalExpressionOperator,
    _UnaryExpressionTemplate,
)

if TYPE_CHECKING:
    from loomi.query.descriptor import EntityIdDescriptor
else:
    EntityIdDescriptor = object

T = TypeVar("T", bound=ModelType)
P = TypeVar("P")


@dataclass(frozen=True)
class AliasedModel:
    """
    Model proxy allowing the same model type to be referenced multiple times with different
    variable names in queries.
    """

    _alias: str
    _model_type: ModelType

    def __getattribute__(self, name: str) -> Any:
        from loomi.query.descriptor import PropertyDescriptor

        if name in ["_model_type", "_alias"]:
            return super().__getattribute__(name)

        if name in self._model_type.model_fields:
            return PropertyDescriptor(
                name, cast(Any, self._model_type.model_fields[name].annotation), self
            )

        raise ModelError("Aliased models only expose property descriptors")


def _validate_property_descriptor(maybe_property_descriptor: Any) -> None:
    from loomi.query.descriptor import EntityIdDescriptor, PropertyDescriptor, _Descriptor

    if not isinstance(maybe_property_descriptor, (PropertyDescriptor, EntityIdDescriptor)):
        raise QueryError(
            f"Expected instance of subclass of {_Descriptor.__class__.__name__}, "
            f"got {maybe_property_descriptor}"
        )


def create_alias(model_type: T, alias: str) -> T:
    """
    Creates a new `AliasedModel` instance which can be used to reference the same model type
    multiple times under different variables in the same query.

    Args:
        model_type: (ModelType): The model to create a alias for.
        alias (str): The alias which will be used in queries. Can be any string which does
        **not match** the format **v<any number>**.

    Raises:
        QueryError: If attempting to use the reserved format for the alias.

    Returns:
        AliasedModel: The model which can be used in queries.
    """
    if re.match(r"^v\d+", alias):
        raise QueryError("Aliases with a pattern 'v<number>' are reserved for internal use")

    return cast(T, AliasedModel(alias, model_type))


def equals(property_descriptor: Any, value: Any) -> QueryExpression:
    """
    Builds a `=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Any): The value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    return QueryExpression(property_descriptor, _ExpressionTemplate.EQ, value)


def not_equals(property_descriptor: Any, value: Any) -> QueryExpression:
    """
    Builds a `<>` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Any): The value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    return QueryExpression(property_descriptor, _ExpressionTemplate.NEQ, value)


def greater_than(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `>` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {_ExpressionTemplate.GT.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.GT, value)


def greater_than_or_equal(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `>=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {_ExpressionTemplate.GTE.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.GTE, value)


def less_than(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `<` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {_ExpressionTemplate.LT.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.LT, value)


def less_than_or_equal(property_descriptor: Any, value: NumericValue) -> QueryExpression:
    """
    Builds a `<=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Union[int, float]): The (numeric) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, (int, float)):
        raise QueryError(
            f"Values for {_ExpressionTemplate.LTE.name} expressions must be valid numbers"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.LTE, value)


def not_(
    expression: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> InvertQueryExpression:
    """
    Builds a `NOT(...)` expression for a query builder.

    Args:
        expression (Union[CompoundQueryExpression, _BaseQueryExpression]): The expression
        to invert.

    Returns:
        InvertQueryExpression: A expression which can be compiled by a query builder.
    """
    return InvertQueryExpression(expression)


def and_(
    *expressions: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> CompoundQueryExpression:
    """
    Builds a `AND(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundQueryExpression, _BaseQueryExpression]): The expressions
        to join.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(_LogicalExpressionOperator.AND, [*expressions])


def or_(
    *expressions: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> CompoundQueryExpression:
    """
    Builds a `OR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundQueryExpression, _BaseQueryExpression]): The expressions
        to join.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(_LogicalExpressionOperator.OR, [*expressions])


def xor(
    *expressions: Union[CompoundQueryExpression, _BaseQueryExpression],
) -> CompoundQueryExpression:
    """
    Builds a `XOR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundQueryExpression, _BaseQueryExpression]): The expressions
        to join.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(_LogicalExpressionOperator.XOR, [*expressions])


def is_null(property_descriptor: Any) -> NullQueryExpression:
    """
    Builds a `IS NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    return NullQueryExpression(
        property_descriptor,
        _UnaryExpressionTemplate.IS_NULL,
    )


def is_not_null(property_descriptor: Any) -> NullQueryExpression:
    """
    Builds a `IS NOT NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    return NullQueryExpression(
        property_descriptor,
        _UnaryExpressionTemplate.IS_NOT_NULL,
    )


def in_(property_descriptor: Any, value: List[Any]) -> QueryExpression:
    """
    Builds a `IN` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (List[Any]): The (list) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, list):
        raise QueryError(
            f"Values for {_ExpressionTemplate.IN.name} expressions must be valid lists"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.IN, value)


def starts_with(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `STARTS WITH` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, str):
        raise QueryError(
            f"Values for {_ExpressionTemplate.STARTS_WITH.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.STARTS_WITH, value)


def ends_with(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `ENDS WITH` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, str):
        raise QueryError(
            f"Values for {_ExpressionTemplate.ENDS_WITH.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.ENDS_WITH, value)


def contains(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `CONTAINS` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, str):
        raise QueryError(
            f"Values for {_ExpressionTemplate.CONTAINS.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.CONTAINS, value)


def regex(property_descriptor: Any, value: str) -> QueryExpression:
    """
    Builds a `=~` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

    Returns:
        QueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    if not isinstance(value, str):
        raise QueryError(
            f"Values for {_ExpressionTemplate.REGEX.name} expressions must be valid strings"
        )

    return QueryExpression(property_descriptor, _ExpressionTemplate.REGEX, value)


def cypher(
    template: str, model_references: Dict[str, QueryModelType], parameters: Dict[str, Any]
) -> CustomQueryExpression:
    """
    Builds a custom Cypher query by injecting the corresponding model variables and parameters into
    the provided template.

    Args:
        template (str): The Cypher query to build. The template can contain placeholders which need
        to correspond to keys from either `model_references` or `parameters`.
        model_references (Dict[str, QueryModelType]): A dict which maps placeholders to their
        models.
        parameters (Dict[str, Any]): A dict which maps placeholders to their parameter values.

    Returns:
        CustomQueryExpression: A expression which can be compiled by a query builder.
    """
    return CustomQueryExpression(template, model_references, parameters)


def all_(property_descriptor: List[P]) -> P:
    """
    Marks this list property to use `ALL` when a query builder encounters it.

    Returns:
        PropertyDescriptor: A property descriptor which can be used to further define paths.
    """
    from loomi.query.descriptor import PropertyDescriptor, _ListPathOperator

    _validate_property_descriptor(property_descriptor)
    descriptor = cast(PropertyDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        PropertyDescriptor(
            f"{descriptor._full_path}.{_ListPathOperator.ALL.value}",
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
    from loomi.query.descriptor import PropertyDescriptor, _ListPathOperator

    _validate_property_descriptor(property_descriptor)
    descriptor = cast(PropertyDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        PropertyDescriptor(
            f"{descriptor._full_path}.{_ListPathOperator.ANY.value}",
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
    from loomi.query.descriptor import PropertyDescriptor, _ListPathOperator

    _validate_property_descriptor(property_descriptor)
    descriptor = cast(PropertyDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        PropertyDescriptor(
            f"{descriptor._full_path}.{_ListPathOperator.NONE.value}",
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
    from loomi.query.descriptor import PropertyDescriptor, _ListPathOperator

    _validate_property_descriptor(property_descriptor)
    descriptor = cast(PropertyDescriptor, property_descriptor)

    current_type = descriptor._annotation
    origin = get_origin(current_type)
    args = get_args(current_type)

    inferred_type = Any
    if origin in (list, List, Union):
        inferred_type = next((a for a in args if a is not type(None)), Any)

    return cast(
        P,
        PropertyDescriptor(
            f"{descriptor._full_path}.{_ListPathOperator.SINGLE.value}",
            inferred_type,
            descriptor._model_type,
        ),
    )


def element_id(model_type: QueryModelType, server_type: ServerType) -> EntityIdDescriptor:
    """
    Builds a descriptor which will be resolved to an `elementId` expression when used by a
    query builder.

    Args:
        model_type: (QueryModelType): The model to create a `elementId` expression for.

    Returns:
        EntityIdDescriptor: A entity id descriptor which can be used by a query builder.
    """
    from loomi.query.descriptor import EntityIdDescriptor, _EntityIdTemplate

    return EntityIdDescriptor(_EntityIdTemplate.ELEMENT_ID, model_type, server_type)


def id_(model_type: QueryModelType, server_type: ServerType) -> EntityIdDescriptor:
    """
    Builds a descriptor which will be resolved to an `id` expression when used by a
    query builder.

    Args:
        model_type: (QueryModelType): The model to create a `id` expression for.

    Returns:
        EntityIdDescriptor: A entity id descriptor which can be used by a query builder.
    """
    from loomi.query.descriptor import EntityIdDescriptor, _EntityIdTemplate

    return EntityIdDescriptor(_EntityIdTemplate.ID, model_type, server_type)
