import logging
from datetime import datetime, timezone
from typing import Dict, List, cast

from loomi.constants import ServerType
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.protocols import CompilableDescriptor
from loomi.query_api.constants import OrderBy
from loomi.query_api.functions.arithmetic import add
from loomi.query_api.functions.collection import any_, single
from loomi.query_api.functions.comparison import and_, equals, greater_than, not_, starts_with
from loomi.query_api.functions.transformation import abs_, ceil, create_db_function, floor, to_upper

logging.basicConfig(level=logging.INFO)


import neo4j
from pydantic import BaseModel, Field

from loomi import Client, Node, Relationship


class Timestamp(BaseModel):
    value: datetime
    metadata: Dict[str, str]


class Event(BaseModel):
    name: str
    timestamps: List[Timestamp]


class Metadata(BaseModel):
    type: int


class Adult(Node):
    name: str
    age: int
    events: List[Event]
    metadata: Metadata


# Initialize the driver like usual
driver = neo4j.GraphDatabase.driver(
    uri="bolt://localhost:7687", auth=("neo4j", "e7aZLc8uE2FaqLNJpCJCwVkh")
)

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")
    session.run(
        "CREATE (n:Test $data)",
        {
            "data": {
                "username": "alice_wonder",
                "id": 10492,
                "active": True,
                "score": 98.5,
                "tags": ["admin", "developer"],
                "metadata": {
                    "login_count": 12,
                    "last_login": datetime.now(timezone.utc),
                },
            }
        },
    )

# client = Client(driver)

# # Register models which the client should resolve
# client.register(Child, Adult, FamilyRelation)
# client.initialize()

# with client.session() as session:
#     session.run("MATCH (n) DETACH DELETE n")
#     for num in [1, 2, 3]:
#         session.run(
#             "CREATE (a:Adult $adult)-[r:IS_PARENT_OF $relation]->(c:Human:Child $child)",
#             {
#                 "adult": {"name": f"John{num}", "age": 28 + num, "job": "Developer"},
#                 "child": {
#                     "name": f"Holly{num}",
#                     "age": 5 + num,
#                 },
#                 "relation": {"loves_child": num % 2 == 0},
#             },
#         )

# result = client.update(Adult).set_(Adult.name, to_upper(Adult.name)).execute()
# print(result)

# models = client.query(Adult).execute()

# ctx = CompilationContext(ServerType.NEO4J)
# ctx.add_model(Adult)

# normal_descriptor = Adult.name
# normal_descriptor_compiled = cast(CompilableDescriptor, normal_descriptor)._compile_descriptor(ctx)

# nested_descriptor = Adult.metadata.type
# nested_descriptor_compiled = cast(CompilableDescriptor, nested_descriptor)._compile_descriptor(ctx)

# nested_list_descriptor = any_(any_(Adult.events).timestamps).value
# nested_list_descriptor_compiled = cast(
#     CompilableDescriptor, nested_list_descriptor
# )._compile_descriptor(ctx)


# db_func = any_(any_(Adult.events).timestamps).value == 2
# db_func = any_(any_(Adult.events).timestamps).value == Adult.events[1].timestamps[0].value
# db_func = add(1, 1)
# db_func = Adult.age + Adult.age
# db_func = to_upper(Adult.age)
# db_func = to_upper("a")
# db_func = to_upper(any_(Adult.events))
# compiled = db_func._compile_db_function(ctx)

# expr = add(Adult.age, 1)
# expr = add(Adult.age, Adult.age)
# expr = add(1, 2)
# expr = add(floor(Adult.age), floor(Adult.age))
# expr = add(ceil(floor(Adult.age)), ceil(floor(Adult.age)))
# expr = add(floor(1), floor(2))
# expr = equals(any_(any_(Adult.events).timestamps).value, 1)
# expr = equals(any_(any_(Adult.events).timestamps).value, add(Adult.age, 2))
# expr = equals(add(Adult.age, 2), add(Adult.age, 2))
# expr = not_(equals(add(Adult.age, 2), add(Adult.age, 2)))
# expr = not_(equals(any_(any_(Adult.events).timestamps).value, add(Adult.age, 2)))
# expr = and_(
#     equals(any_(any_(Adult.events).timestamps).value, add(Adult.age, 2)),
#     equals(any_(single(Adult.events).timestamps).value, Adult.age),
#     equals(Adult.name, "foo"),
# )
# expr = add(Adult.age, add(Adult.age, 2))
# expr = add(1, any_(any_(Adult.events).timestamps).value)

# compiled = expr._compile_expression(ctx)
# query = compiled.outer_template.format(innermost_template=compiled.expression_template)
# query = expr.to_query_string(ctx)

print()


# 'any(v1 IN v0.events WHERE any(v2 IN v1.timestamps WHERE {innermost_template}))'
