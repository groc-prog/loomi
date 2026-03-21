import re
from dataclasses import dataclass
from typing import Any, Dict, List, TypeVar, Union, cast

from loomi._internal._types import _ModelType, _NumericValue, _QueryModelType
from loomi.exceptions import QueryError
from loomi.query.expressions import (
    CompoundQueryExpression,
    CustomQueryExpression,
    QueryExpression,
    UnaryQueryExpression,
    _BaseQueryExpression,
    _ExpressionTemplate,
    _LogicalExpressionOperator,
    _UnaryExpressionTemplate,
)

T = TypeVar("T", bound=_ModelType)


@dataclass(frozen=True)
class AliasedModel:
    """
    Model proxy allowing the same model type to be referenced multiple times with different
    variable names in queries.
    """

    _alias: str
    _model_type: _ModelType

    def __getattribute__(self, name: str) -> Any:
        from loomi.query.property_descriptor import PropertyDescriptor

        if name in self._model_type.model_fields:
            return PropertyDescriptor(name, self._model_type.model_fields[name].annotation, self)

        return super().__getattribute__(name)


def _validate_property_descriptor(maybe_property_descriptor: Any) -> None:
    from loomi.query.property_descriptor import PropertyDescriptor

    if not isinstance(maybe_property_descriptor, PropertyDescriptor):
        raise QueryError(
            f"Expected {PropertyDescriptor.__class__.__name__}, got {maybe_property_descriptor}"
        )


def create_alias(model_type: T, alias: str) -> T:
    """
    Creates a new `AliasedModel` instance which can be used to reference the same model type
    multiple times under different variables in the same query.

    Args:
        model_type: (Union[Type[Node], Type[Relationship]]): The model to create a alias for.
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


def greater_than(property_descriptor: Any, value: _NumericValue) -> QueryExpression:
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


def greater_than_or_equal(property_descriptor: Any, value: _NumericValue) -> QueryExpression:
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


def less_than(property_descriptor: Any, value: _NumericValue) -> QueryExpression:
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


def less_than_or_equal(property_descriptor: Any, value: _NumericValue) -> QueryExpression:
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
) -> CompoundQueryExpression:
    """
    Builds a `NOT(...)` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        CompoundQueryExpression: A expression which can be compiled by a query builder.
    """
    return CompoundQueryExpression(_LogicalExpressionOperator.NOT, [expression])


def is_null(property_descriptor: Any) -> UnaryQueryExpression:
    """
    Builds a `IS NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    return UnaryQueryExpression(
        property_descriptor,
        _UnaryExpressionTemplate.IS_NULL,
    )


def is_not_null(property_descriptor: Any) -> UnaryQueryExpression:
    """
    Builds a `IS NOT NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    _validate_property_descriptor(property_descriptor)

    return UnaryQueryExpression(
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
    template: str, model_references: Dict[str, _QueryModelType], parameters: Dict[str, Any]
) -> CustomQueryExpression:
    """
    Builds a custom Cypher query by injecting the corresponding model variables and parameters into
    the provided template.

    Args:
        template (str): The Cypher query to build. The template can contain placeholders which need
        to correspond to keys from either `model_references` or `parameters`.
        model_references (Dict[str, _QueryModelType]): A dict which maps placeholders to their
        models.
        parameters (Dict[str, Any]): A dict which maps placeholders to their parameter values.

    Returns:
        CustomQueryExpression: A expression which can be compiled by a query builder.
    """
    return CustomQueryExpression(template, model_references, parameters)
