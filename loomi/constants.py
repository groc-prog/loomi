import datetime
from enum import StrEnum

import neo4j.spatial
import neo4j.time


class ServerType(StrEnum):
    """The supported server types."""

    NEO4J = "Neo4j"
    MEMGRAPH = "Memgraph"


SUPPORTED_DATA_TYPES = (
    bool,
    int,
    float,
    str,
    bytes,
    bytearray,
    list,
    dict,
    type(None),
    neo4j.time.Date,
    neo4j.time.Time,
    neo4j.time.DateTime,
    neo4j.time.Duration,
    neo4j.spatial.Point,
    datetime.date,
    datetime.time,
    datetime.datetime,
    datetime.timedelta,
)

SUPPORTED_LIST_DATA_TYPES = (
    bool,
    int,
    float,
    str,
    bytes,
    bytearray,
    neo4j.time.Date,
    neo4j.time.Time,
    neo4j.time.DateTime,
    neo4j.time.Duration,
    neo4j.spatial.Point,
    datetime.date,
    datetime.time,
    datetime.datetime,
    datetime.timedelta,
)
