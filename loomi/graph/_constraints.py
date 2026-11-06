from enum import StrEnum
from typing import Dict

# TODO: These are currently unused and will be used when implementing
# migrations


class Neo4jConstraintType(StrEnum):
    UNIQUENESS = "UNIQUENESS"
    RELATIONSHIP_UNIQUENESS = "RELATIONSHIP_UNIQUENESS"


class MemgraphConstraintType(StrEnum):
    EXISTS = "exists"
    UNIQUE = "unique"
    DATA_TYPE = "data_type"


class DataTypeConstraintType(StrEnum):
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


_MEMGRAPH_DATA_TYPE_MAPPING: Dict[str, str] = {
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
