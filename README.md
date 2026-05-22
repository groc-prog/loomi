# Loomi

[![CI](https://github.com/yourusername/loomi/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/loomi/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/pypi/pyversions/loomi)](https://pypi.org/project/loomi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A minimalistic Python Object-Graph Mapper designed to handle the most common tasks when working with **Neo4j** or **Memgraph**.

## Features

- **Hybrid Sync/Async Architecture:** Built around the driver provided by the [`neo4j`](https://pypi.org/project/neo4j/), loomi supports both sync and async clients.
- **Dual-Database Support:** Compatibility with both Neo4j and Memgraph out of the box.
- **Type Safety:** Fully typed models and queries thanks to [`pydantic`](https://pydantic.dev/docs/).
- **Compatibility out of the box:** Drop-in replacement when you already use the driver provided by the [`neo4j`](https://pypi.org/project/neo4j/) package. Enable additional features as required.

---

## Installation

Install via `pip` or your favorite package manager:
```bash
pip install loomi
```

Or with poetry:
```bash
poetry add loomi
```

## Quick Start
### 1. Define Your Schema

```python
from loomi import Node, Relationship
from pydantic import Field

class Child(Node):
  name: str
  age: int

  # Define how the node is displayed in the database
  loomi_config = {
    "labels": {"Human", "Child"}
  }


class Adult(Node):
  name: str
  age: int
  job: str


class FamilyRelation(Relationship):
  loves_child: bool = Field(default=True)

  # Define how the relationship is displayed in the database
  loomi_config = {
    "type": "IS_PARENT_OF"
  }
```

### 2. Connect and Query

```python
import asyncio
import neo4j
from loomi import AsyncClient

# Initialize the driver like usual
driver = neo4j.AsyncGraphDatabase.driver(
  uri="bolt://localhost:7687", auth=("neo4j", "password")
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

## Local Development & Testing

This project uses [Poetry](https://python-poetry.org/) to manage dependencies and virtual environments.

### 1. Setup Environment

```bash
git clone [https://github.com/yourusername/loomi.git](https://github.com/yourusername/loomi.git)
cd loomi

poetry install
poetry run pre-commit install
```

### 2. Run Database Containers

```bash
docker compose up -d
```

### 3. Run the Test Suite

```bash
poetry run pytest tests/
```
