from typing import Any, Callable, List

from loomi.exceptions import QueryError
from loomi.query_api._core.db_function import DbFunction
from loomi.query_api._core.protocols import CompilableDbFunction
from loomi.query_api._core.templates import DbFunctionTemplate


def tail(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `tail()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.TAIL, [])


def abs_(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `abs()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.ABS, [])


def ceil(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `ceil()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.CEIL, [])


def floor(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `floor()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.FLOOR, [])


def round_(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `round()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.ROUND, [])


def ltrim(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `ltrim()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.LTRIM, [])


def rtrim(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `rtrim()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.RTRIM, [])


def trim(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `trim()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.TRIM, [])


def to_lower(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `toLower()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.TO_LOWER, [])


def to_upper(to_wrap: Any) -> CompilableDbFunction:
    """
    Wraps the descriptor or value in a `toUpper()` function.

    Args:
        to_wrap (Any): The descriptor or DB function to build the expression for.

    Returns:
        CompilableDbFunction: A transformer which can be compiled by a query builder.
    """
    return DbFunction(to_wrap, DbFunctionTemplate.TO_UPPER, [])


def create_db_function(template: str) -> Callable[[Any, List[Any]], DbFunction]:
    """
    Creates a new database function which can be compiled with queries.

    The template must include a `variable_or_parameter` placeholder which will hold either a
    parameter or the model variable. Additionally, one or more arguments can be provided
    with `arg<num>` placeholders.

    Args:
        template (str): The template to use in the database function.

    Raises:
        QueryError: If the required placeholder is missing.

    Returns:
        DbFunction: A compilable database function.
    """
    if "variable_or_parameter" not in template:
        raise QueryError(
            "'variable_or_parameter' placeholder must be present in custom database functions"
        )

    return lambda to_wrap, *args: DbFunction(to_wrap, template, *args)
