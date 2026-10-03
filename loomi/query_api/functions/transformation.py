from typing import Any

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
