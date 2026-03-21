from enum import StrEnum


class Neo4jIndexType(StrEnum):
    """Index types supported by Neo4j."""

    RANGE = "RANGE"
    TEXT = "TEXT"
    POINT = "POINT"
    TOKEN_LOOKUP = "TOKEN_LOOKUP"
    FULLTEXT = "FULLTEXT"
    VECTOR = "VECTOR"


class MemgraphIndexType(StrEnum):
    """Index types supported by Memgraph."""

    LABEL = "label"
    LABEL_AND_PROPERTY = "label+property"
    EDGE_TYPE = "edge-type"
    EDGE_TYPE_AND_PROPERTY = "edge-type+property"
    EDGE_AND_PROPERTY = "edge-property"
    POINT = "point"
