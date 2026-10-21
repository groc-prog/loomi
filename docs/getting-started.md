# Getting started with `loomi`

> [!TIP]
> This package is designed to be a **drop-in replacement**. If you are already using the [`neo4j package`](https://pypi.org/project/neo4j/), you can get started with loomi without any changes to how your code behaves. Enable additional features as needed.

## 1. Define your schema

```python
from loomi import Node, Relationship
from pydantic import Field

# Nodes and relationships are defined as normal classes
# Any properties are translated to database entity properties
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
import asyncio
import neo4j
from loomi import AsyncClient

# Initialize the driver like usual
driver = neo4j.AsyncGraphDatabase.driver(
  uri="<uri>", auth=("<user>", "<password>")
)
client = AsyncClient(driver)

# Register models which the client should resolve
client.register(Child, Adult, FamilyRelation)

async def main():
  await client.initialize()

  async with client.session() as session:
    # Create some sample data
    await session.run(
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

    # Query the database like you would usually
    result = await session.run(
      "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
    )

    # `result` provides the same interface as the native result
    # with some loomi-specific additions
    models = await result.values()

    # Prints [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
    print(models)


if __name__ == "__main__":
  asyncio.run(main())
```
