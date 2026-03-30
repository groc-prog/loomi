from enum import StrEnum
from typing import Dict


class ExpressionTemplate(StrEnum):
    """Templates for query expressions."""

    EQ = "{variable} = {parameter}"
    NEQ = "{variable} <> {parameter}"
    GT = "{variable} > {parameter}"
    GTE = "{variable} >= {parameter}"
    LT = "{variable} < {parameter}"
    LTE = "{variable} <= {parameter}"
    IN = "{variable} IN {parameter}"
    STARTS_WITH = "{variable} STARTS WITH {parameter}"
    ENDS_WITH = "{variable} ENDS WITH {parameter}"
    CONTAINS = "{variable} CONTAINS {parameter}"
    REGEX = "{variable} =~ {parameter}"


class UnaryExpressionTemplate(StrEnum):
    """Templates for unary query expressions."""

    IS_NULL = "{variable} IS NULL"
    IS_NOT_NULL = "{variable} IS NOT NULL"


class LogicalExpressionOperator(StrEnum):
    """Templates for logical query expressions."""

    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"


class EntityIdExpressionTemplate(StrEnum):
    """Templates for entity ID query expressions."""

    ELEMENT_ID = "elementId({variable})"
    ID = "id({variable})"


class ListPathOperator(StrEnum):
    """Operators for list paths."""

    ANY = "$any"
    ALL = "$all"
    NONE = "$none"
    SINGLE = "$single"


ListPathOperatorTemplate: Dict[str, str] = {
    ListPathOperator.ANY.value: "any",
    ListPathOperator.ALL.value: "all",
    ListPathOperator.NONE.value: "none",
    ListPathOperator.SINGLE.value: "single",
}


class DbFunctionTemplate(StrEnum):
    """Templates for DB functions."""

    TAIL = "tail({variable})"
    ABS = "abs({variable})"
    CEIL = "ceil({variable})"
    FLOOR = "floor({variable})"
    ROUND = "round({variable})"
    LTRIM = "ltrim({variable})"
    RTRIM = "rtrim({variable})"
    TRIM = "trim({variable})"
    TO_LOWER = "toLower({variable})"
    TO_UPPER = "toUpper({variable})"
