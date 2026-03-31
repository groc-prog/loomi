from enum import StrEnum


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


class DbFunctionTemplate(StrEnum):
    """Templates for DB functions."""

    TAIL = "tail({variable_or_parameter})"
    ABS = "abs({variable_or_parameter})"
    CEIL = "ceil({variable_or_parameter})"
    FLOOR = "floor({variable_or_parameter})"
    ROUND = "round({variable_or_parameter})"
    LTRIM = "ltrim({variable_or_parameter})"
    RTRIM = "rtrim({variable_or_parameter})"
    TRIM = "trim({variable_or_parameter})"
    TO_LOWER = "toLower({variable_or_parameter})"
    TO_UPPER = "toUpper({variable_or_parameter})"
