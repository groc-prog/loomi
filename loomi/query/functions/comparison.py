from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi._internal.types import NumericValue, QueryModelType
from loomi.exceptions import QueryError
from loomi.query._templates import (
    ExpressionTemplate,
    LogicalExpressionTemplate,
    UnaryExpressionTemplate,
)
from loomi.query.descriptors import FieldDescriptor
from loomi.query.expressions import (
    CompoundExpression,
    CustomCypherExpression,
    Expression,
    InvertExpression,
    NullExpression,
    _BaseExpression,
)

if TYPE_CHECKING:
    from loomi.query.db_function import DbFunction
else:
    DbFunction = object


def equals(property_descriptor: Any, value: Any) -> Expression:
    """
    Builds a `=` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Any): The value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.EQ, value)


def not_equals(property_descriptor: Any, value: Any) -> Expression:
    """
    Builds a `<>` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (Any): The value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.NEQ, value)


def greater_than(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `>` expression for a query builder.

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

    return Expression(property_descriptor, ExpressionTemplate.GT, value)


def greater_than_or_equal(
    property_descriptor: Any, value: Union[NumericValue, DbFunction]
) -> Expression:
    """
    Builds a `>=` expression for a query builder.

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

    return Expression(property_descriptor, ExpressionTemplate.GTE, value)


def less_than(property_descriptor: Any, value: Union[NumericValue, DbFunction]) -> Expression:
    """
    Builds a `<` expression for a query builder.

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

    return Expression(property_descriptor, ExpressionTemplate.LT, value)


def less_than_or_equal(
    property_descriptor: Any, value: Union[NumericValue, DbFunction]
) -> Expression:
    """
    Builds a `<=` expression for a query builder.

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

    return Expression(property_descriptor, ExpressionTemplate.LTE, value)


def not_(
    expression: Union[CompoundExpression, _BaseExpression],
) -> InvertExpression:
    """
    Builds a `NOT(...)` expression for a query builder.

    Args:
        expression (Union[CompoundExpression, _BaseExpression]): The expression
        to invert.

    Returns:
        InvertExpression: A expression which can be compiled by a query builder.
    """
    return InvertExpression(expression)


def and_(
    *expressions: Union[CompoundExpression, _BaseExpression],
) -> CompoundExpression:
    """
    Builds a `AND(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, _BaseExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    return CompoundExpression(LogicalExpressionTemplate.AND, [*expressions])


def or_(
    *expressions: Union[CompoundExpression, _BaseExpression],
) -> CompoundExpression:
    """
    Builds a `OR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, _BaseExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    return CompoundExpression(LogicalExpressionTemplate.OR, [*expressions])


def xor(
    *expressions: Union[CompoundExpression, _BaseExpression],
) -> CompoundExpression:
    """
    Builds a `XOR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, _BaseExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    return CompoundExpression(LogicalExpressionTemplate.XOR, [*expressions])


def is_null(property_descriptor: Any) -> NullExpression:
    """
    Builds a `IS NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return NullExpression(
        property_descriptor,
        UnaryExpressionTemplate.IS_NULL,
    )


def is_not_null(property_descriptor: Any) -> NullExpression:
    """
    Builds a `IS NOT NULL` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        UnaryQueryExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(property_descriptor, FieldDescriptor):
        raise QueryError(
            f"Descriptor must be a valid field descriptor. Expected {FieldDescriptor.__name__} "
            f", got {property_descriptor}"
        )

    return NullExpression(
        property_descriptor,
        UnaryExpressionTemplate.IS_NOT_NULL,
    )


def in_(property_descriptor: Any, value: Union[List[Any], DbFunction]) -> Expression:
    """
    Builds a `IN` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (List[Any]): The (list) value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.IN, value)


def starts_with(property_descriptor: Any, value: Union[str, DbFunction]) -> Expression:
    """
    Builds a `STARTS WITH` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.STARTS_WITH, value)


def ends_with(property_descriptor: Any, value: Union[str, DbFunction]) -> Expression:
    """
    Builds a `ENDS WITH` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.ENDS_WITH, value)


def contains(property_descriptor: Any, value: Union[str, DbFunction]) -> Expression:
    """
    Builds a `CONTAINS` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.CONTAINS, value)


def regex(property_descriptor: Any, value: Union[str, DbFunction]) -> Expression:
    """
    Builds a `=~` expression for a query builder.

    Args:
        property_descriptor (PropertyDescriptor): The descriptor to build the expression for.
        value (str): The (string) value used in the expression.

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

    return Expression(property_descriptor, ExpressionTemplate.REGEX, value)


def cypher(
    template: str, model_map: Dict[str, QueryModelType], parameter_map: Dict[str, Any]
) -> CustomCypherExpression:
    """
    Builds a special query expression which can contain custom Cypher expressions. The resulting
    expression can contain any valid Cypher expressions.

    [!NOTE] Parameter placeholders **must not** include the `$` prefix

    Args:
        template (str): The custom expression used as a template.
        model_map (Dict[str, QueryModelType]): A map of template placeholders and their
        corresponding models. At compile time, the placeholders will be replaced with their actual
        variable names.
        parameter_map (Dict[str, Any]): A map of template placeholders and their corresponding
        parameter values. At compile time, the placeholders will be replaced with their actual
        parameter names.

    Returns:
        Expression: A expression which can be compiled by a query builder.
    """
    return CustomCypherExpression(template, model_map, parameter_map)
