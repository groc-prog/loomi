from enum import StrEnum
from typing import Dict


class Neo4jConstraintType(StrEnum):
    """Constraint types supported by Neo4j."""

    UNIQUENESS = "UNIQUENESS"
    RELATIONSHIP_UNIQUENESS = "RELATIONSHIP_UNIQUENESS"


class MemgraphConstraintType(StrEnum):
    """Constraint types supported by Memgraph."""

    EXISTS = "exists"
    UNIQUE = "unique"
    DATA_TYPE = "data_type"


class DataTypeConstraintType(StrEnum):
    """Constraint data types supported by Memgraph."""

    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    LIST = "LIST"
    MAP = "MAP"
    DURATION = "DURATION"
    DATE = "DATE"
    LOCAL_TIME = "LOCALTIME"
    LOCAL_DATETIME = "LOCALDATETIME"
    ZONED_DATETIME = "ZONEDDATETIME"
    ENUM = "ENUM"
    POINT = "POINT"


_MemgraphDataTypeMapping: Dict[str, str] = {
    "LIST": DataTypeConstraintType.LIST.value,
    "MAP": DataTypeConstraintType.MAP.value,
    "DURATION": DataTypeConstraintType.DURATION.value,
    "DATE": DataTypeConstraintType.DATE.value,
    "INTEGER": DataTypeConstraintType.INTEGER.value,
    "FLOAT": DataTypeConstraintType.FLOAT.value,
    "STRING": DataTypeConstraintType.STRING.value,
    "BOOL": DataTypeConstraintType.BOOLEAN.value,
    "LOCAL TIME": DataTypeConstraintType.LOCAL_TIME.value,
    "LOCAL DATE TIME": DataTypeConstraintType.LOCAL_DATETIME.value,
    "ZONED DATE TIME": DataTypeConstraintType.ZONED_DATETIME.value,
    "ENUM": DataTypeConstraintType.ENUM.value,
    "POINT": DataTypeConstraintType.POINT.value,
}
