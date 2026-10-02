from enum import StrEnum


class OrderBy(StrEnum):
    """ORDER BY values for Cypher."""

    DESC = "DESC"
    ASC = "ASC"
