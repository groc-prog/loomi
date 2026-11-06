from enum import StrEnum


class ExpressionTemplate(StrEnum):
    EQ = "{left} = {right}"
    NEQ = "{left} <> {right}"
    GT = "{left} > {right}"
    GTE = "{left} >= {right}"
    LT = "{left} < {right}"
    LTE = "{left} <= {right}"
    IN = "{left} IN {right}"
    STARTS_WITH = "{left} STARTS WITH {right}"
    ENDS_WITH = "{left} ENDS WITH {right}"
    CONTAINS = "{left} CONTAINS {right}"
    REGEX = "{left} =~ {right}"
    IS_NULL = "{left} IS NULL"
    IS_NOT_NULL = "{left} IS NOT NULL"


class ArithmeticExpressionTemplate(StrEnum):
    ADD = "{left} + {right}"
    R_ADD = "{right} + {left}"
    SUBTRACT = "{left} - {right}"
    R_SUBTRACT = "{right} - {left}"
    MULTIPLY = "{left} * {right}"
    R_MULTIPLY = "{right} * {left}"
    DIVIDE = "{left} / {right}"
    R_DIVIDE = "{right} / {left}"
    MODULO = "{left} % {right}"
    R_MODULO = "{right} % {left}"
    POW = "{left} ^ {right}"
    R_POW = "{right} ^ {left}"


class LogicalExpressionTemplate(StrEnum):
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    NOT = "NOT"


class EntityIdExpressionTemplate(StrEnum):
    ELEMENT_ID = "elementId({variable})"
    ID = "id({variable})"


class DbFunctionTemplate(StrEnum):
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
