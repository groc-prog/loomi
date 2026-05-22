import datetime
from typing import Annotated, cast

from pydantic import BaseModel, Field

from loomi.graph.annotations import (
    DataTypeConstraint,
    ExistenceConstraint,
    PointIndex,
    PropertyIndex,
    RangeIndex,
    TextIndex,
    UniquenessConstraint,
    VectorIndex,
)
from loomi.graph.constraints import DataTypeConstraintType
from loomi.graph.node import Node
from loomi.migrations._schema import MigrationSchemaFactory
from loomi.migrations.settings import MigrationSettings

# class Before(Node):
#     prop1: Annotated[str, UniquenessConstraint()] = Field(default="foo")
#     prop2: Annotated[str, ExistenceConstraint()]
#     prop3: Annotated[str, DataTypeConstraint(data_type=DataTypeConstraintType.STRING)]
#     prop4: Annotated[str, PropertyIndex()]
#     prop5: Annotated[str, RangeIndex()]
#     prop6: Annotated[str, TextIndex()]
#     prop7: Annotated[str, PointIndex()]
#     prop8: Annotated[str, VectorIndex()]


# class After(Node):
#     prop1: Annotated[str, UniquenessConstraint()] = Field(default="foo")
#     prop2: Annotated[str, ExistenceConstraint()]
#     prop3: Annotated[str, DataTypeConstraint(data_type=DataTypeConstraintType.STRING)]
#     prop41: Annotated[str, PropertyIndex(composite_key="foo")]
#     prop42: Annotated[str, PropertyIndex(composite_key="foo")]
#     prop43: Annotated[str, PropertyIndex()]
#     prop5: Annotated[str, RangeIndex()]
#     prop6: Annotated[str, TextIndex()]
#     prop7: Annotated[str, PointIndex()]


# before_schema = Before.model_json_schema()
# after_schema = After.model_json_schema()

# s = MigrationSettings()
# c = MigrationSchemaFactory(After)

# ms = c.generate_schema_definition()


class A(Node):
    a: bool
    b: int
    c: float
    d: str
    e: bytes
    g: datetime.date
    h: datetime.time
    i: datetime.datetime
    j: datetime.timedelta
    k: list[str]


m = A.model_json_schema()

pass
