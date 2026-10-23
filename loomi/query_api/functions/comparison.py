from typing import Any, Dict, List, Union

from loomi._core.types import QueryModelType
from loomi.exceptions import QueryError
from loomi.query_api._core.expressions import (
    CompoundExpression,
    CustomCypherExpression,
    Expression,
    InvertExpression,
)
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableDescriptor,
    CompilableExpression,
)
from loomi.query_api._core.templates import ExpressionTemplate, LogicalExpressionTemplate


def _validate_wrapped_value(value: Any, *additional_types: Any) -> None:
    if not isinstance(
        value, (*additional_types, CompilableDescriptor, CompilableDbFunction, CompilableExpression)
    ):
        raise QueryError("Value must be a valid compilable value")


def _validate_value(value: Any, *additional_types: Any) -> None:
    if not isinstance(
        value, (*additional_types, CompilableDescriptor, CompilableDbFunction, CompilableExpression)
    ):
        raise QueryError("Value must be a valid compilable value")

    _validate_non_list_path_descriptor(value)


def _validate_non_list_path_descriptor(value: Any) -> None:
    if not isinstance(value, CompilableDescriptor):
        return

    field_descriptor_fn = getattr(value, "_is_list_path", None)
    if field_descriptor_fn is not None and field_descriptor_fn():
        raise QueryError("Field descriptor with list path operators are not allowed as values")


def equals(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `=` expression for a query builder.

    Args:
        to_wrap (Any): A compilable value.
        value (Any): A compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_non_list_path_descriptor(value)

    return Expression(to_wrap, ExpressionTemplate.EQ, value)


def not_equals(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `<>` expression for a query builder.

    Args:
        to_wrap (Any): A compilable value.
        value (Any): A compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_non_list_path_descriptor(value)

    return Expression(to_wrap, ExpressionTemplate.NEQ, value)


def greater_than(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `>` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap, int, float)
    _validate_value(value, int, float)

    return Expression(to_wrap, ExpressionTemplate.GT, value)


def greater_than_or_equal(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `>=` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap, int, float)
    _validate_value(value, int, float)

    return Expression(to_wrap, ExpressionTemplate.GTE, value)


def less_than(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `<` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap, int, float)
    _validate_value(value, int, float)

    return Expression(to_wrap, ExpressionTemplate.LT, value)


def less_than_or_equal(to_wrap: Any, value: Any) -> CompilableExpression:
    """
    Builds a `<=` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.
        value (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_wrapped_value(to_wrap, int, float)
    _validate_value(value, int, float)

    return Expression(to_wrap, ExpressionTemplate.LTE, value)


def not_(
    expression: Union[CompoundExpression, CompilableExpression],
) -> CompilableExpression:
    """
    Builds a `NOT(...)` expression for a query builder.

    Args:
        expression (Union[CompoundExpression, CompilableExpression]): The expression
        to invert.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    if not isinstance(expression, (CompoundExpression, CompilableExpression)):
        raise QueryError("Value must be a valid expression")

    return InvertExpression(expression)


def and_(
    *expressions: Union[CompoundExpression, CompilableExpression],
) -> CompoundExpression:
    """
    Builds a `AND(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, CompilableExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    if not all(
        isinstance(expression, (CompoundExpression, CompilableExpression))
        for expression in expressions
    ):
        raise QueryError("All values must be valid expressions")

    return CompoundExpression(LogicalExpressionTemplate.AND, [*expressions])


def or_(
    *expressions: Union[CompoundExpression, CompilableExpression],
) -> CompoundExpression:
    """
    Builds a `OR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, CompilableExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    if not all(
        isinstance(expression, (CompoundExpression, CompilableExpression))
        for expression in expressions
    ):
        raise QueryError("All values must be valid expressions")

    return CompoundExpression(LogicalExpressionTemplate.OR, [*expressions])


def xor(
    *expressions: Union[CompoundExpression, CompilableExpression],
) -> CompoundExpression:
    """
    Builds a `XOR(...)` expression for a query builder.

    Args:
        *expressions (Union[CompoundExpression, CompilableExpression]): The expressions
        to join.

    Returns:
        CompoundExpression: A expression which can be compiled by a query builder.
    """
    if not all(
        isinstance(expression, (CompoundExpression, CompilableExpression))
        for expression in expressions
    ):
        raise QueryError("All values must be valid expressions")

    return CompoundExpression(LogicalExpressionTemplate.XOR, [*expressions])


def is_null(to_wrap: Any) -> CompilableExpression:
    """
    Builds a `IS NULL` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_non_list_path_descriptor(to_wrap)

    return Expression(to_wrap, ExpressionTemplate.IS_NULL, None)


def is_not_null(to_wrap: Any) -> CompilableExpression:
    """
    Builds a `IS NOT NULL` expression for a query builder.

    Args:
        to_wrap (Any): A numeric or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_non_list_path_descriptor(to_wrap)

    return Expression(to_wrap, ExpressionTemplate.IS_NOT_NULL, None)


def in_(to_wrap: Any, value: Union[List[Any], CompilableDbFunction]) -> CompilableExpression:
    """
    Builds a `IN` expression for a query builder.

    Args:
        to_wrap (Any): A compilable value.
        value (List[Any]): A list or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_value(value, list)

    return Expression(to_wrap, ExpressionTemplate.IN, value)


def starts_with(to_wrap: Any, value: Union[str, CompilableDbFunction]) -> CompilableExpression:
    """
    Builds a `STARTS WITH` expression for a query builder.

    Args:
        to_wrap (Any): A string or compilable value.
        value (str): A string or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_value(to_wrap, str)
    _validate_value(value, str)

    return Expression(to_wrap, ExpressionTemplate.STARTS_WITH, value)


def ends_with(to_wrap: Any, value: Union[str, CompilableDbFunction]) -> CompilableExpression:
    """
    Builds a `ENDS WITH` expression for a query builder.

    Args:
        to_wrap (Any): A string or compilable value.
        value (str): A string or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_value(to_wrap, str)
    _validate_value(value, str)

    return Expression(to_wrap, ExpressionTemplate.ENDS_WITH, value)


def contains(to_wrap: Any, value: Union[str, CompilableDbFunction]) -> CompilableExpression:
    """
    Builds a `CONTAINS` expression for a query builder.

    Args:
        to_wrap (Any): A string or compilable value.
        value (str): A string or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_value(to_wrap, str)
    _validate_value(value, str)

    return Expression(to_wrap, ExpressionTemplate.CONTAINS, value)


def regex(to_wrap: Any, value: Union[str, CompilableDbFunction]) -> CompilableExpression:
    """
    Builds a `=~` expression for a query builder.

    Args:
        to_wrap (Any): A string or compilable value.
        value (str): A string or compilable value.

    Raises:
        QueryError: If the provided descriptor is not valid.

    Returns:
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    _validate_value(to_wrap, str)
    _validate_value(value, str)

    return Expression(to_wrap, ExpressionTemplate.REGEX, value)


def cypher(
    template: str, model_map: Dict[str, QueryModelType], parameter_map: Dict[str, Any]
) -> CompilableExpression:
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
        CompilableExpression: A expression which can be compiled by a query builder.
    """
    return CustomCypherExpression(template, model_map, parameter_map)
