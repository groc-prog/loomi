# Getting started with loomi

> [!TIP]
> loomi is designed to be a **drop-in replacement**. If you are already using the [`neo4j` package](https://pypi.org/project/neo4j/), you can adopt loomi without changing how your existing code behaves. Additional features can be enabled as needed.

## 1. Define your schema

```python
from loomi import Node, Relationship
from pydantic import Field


# Nodes and relationships are defined as regular classes.
# Their class attributes are translated into database entity properties.
class Child(Node):
    name: str
    age: int

    # Define how the entity is displayed in the database
    loomi_config = {
        "labels": {"Human", "Child"}
    }


class Adult(Node):
    name: str
    age: int
    job: str


class FamilyRelation(Relationship):
    loves_child: bool = Field(default=True)

    loomi_config = {
        "type": "IS_PARENT_OF"
    }
```

## 2. Connect and query

```python
import neo4j
from loomi import Client

# Initialize the driver as usual
driver = neo4j.GraphDatabase.driver(
    uri="<uri>", auth=("<user>", "<password>")
)
client = Client(driver)

# Register the models the client should resolve
client.register(Child, Adult, FamilyRelation)
client.initialize()

with client.session() as session:
    # Create some sample data
    session.run(
        "CREATE (a:Adult $adult)-[r:IS_PARENT_OF $relation]->(c:Human:Child $child)",
        {
            "adult": {
                "name": "John",
                "age": 28,
                "job": "Developer"
            },
            "child": {
                "name": "Holly",
                "age": 5,
            },
            "relation": {
                "loves_child": True
            }
        }
    )

    # Query the database as you usually would
    result = session.run(
        "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
    )

    # `result` exposes the same interface as the native result,
    # with some loomi-specific additions
    models = result.values()

    # Prints, for example:
    # [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
    print(models)
```
