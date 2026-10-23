# Model usage and configuration

This section covers how loomi models are defined and configured, and how they are used later in [queries](./sessions-transactions-and-results.md).

## Types of models

loomi has several types of models. Some are defined by the user, while others are only returned by queries and **should never need to be instantiated yourself**:

- `Node`: Represents a type of node in the database.
- `Relationship`: Represents a type of relationship in the database.
- `Graph`: A wrapper around the `neo4j.graph.Graph` class that provides correct typing and logic for working with loomi nodes and relationships. It exposes **the same interface** as the `Graph` class from the `neo4j.graph` module.
- `Path`: A wrapper around the `neo4j.graph.Path` class that provides correct typing and logic for working with loomi nodes and relationships. It exposes **the same interface** as the `Path` class from the `neo4j.graph` module.

## Defining your models

Under the hood, nodes and relationships are just [Pydantic classes](https://pydantic.dev/). If you have worked with Pydantic before, you will recognize how loomi uses Pydantic's capabilities:

```python
from pydantic import Field, field_validator

from loomi import Node, Relationship


# Nodes and relationships are defined as regular classes.
# Their class attributes are translated into database entity properties.
class Child(Node):
    name: str
    age: int


class Adult(Node):
    name: str
    age: int
    job: str

    # Everything Pydantic has to offer is supported
    @field_validator("age")
    @classmethod
    def check_positive_age(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Age must be a positive integer.")
        return value


class FamilyRelation(Relationship):
    loves_child: bool = Field(default=True)
```

### Configuring models

As you may have seen in the [Getting started](../getting-started.md) docs, both nodes and relationships can be configured to behave differently. Some configuration options are shared by both model types:

> [!WARNING]
> When using custom (de)serializer functions, make sure your serialization logic is performant, as this can quickly become a performance trap under heavy use. In most cases, you should _consider switching to Memgraph_ when you make heavy use of nested properties.

> [!WARNING]
> Uniqueness of node labels and relationship types is not checked. The client will use the last model with matching labels or type when transforming results into models.

- **`serializer_fn`**: Only relevant when using Neo4j with `serialize_nested` enabled on the client. Use this to control how nested properties are serialized before they are stored. This function is called for all fields that are not of a **supported data type**, after `model.model_dump()` has been called. By default, `json.dumps` is used.
- **`deserializer_fn`**: Only relevant when using Neo4j with `serialize_nested` enabled on the client. Use this to control how nested properties are deserialized after they are loaded from the database. This function is called for all fields where the data type does not match their annotation on the model. For lists, it is called for each list item. By default, `json.loads` is used.
- **`labels`**: Specific to **nodes**. Defines the labels used when the model is persisted to the database. By default, the **unchanged class name** is used as the only label.
- **`type`**: Specific to **relationships**. Defines the type used when the model is persisted to the database. By default, the **class name** converted into **SCREAMING_SNAKE_CASE** is used as the type.

> [!NOTE]
> Configuration options are always per model type and cannot be defined globally.

#### Supported data types

The **supported data types** referenced by `serializer_fn` and `deserializer_fn` are the types Neo4j and Memgraph can store natively as property values. The following are considered supported:

- Python built-ins: `bool`, `int`, `float`, `str`, `bytes`, `bytearray`, `list`, `dict`, and `NoneType`
- Neo4j temporal and spatial types: `neo4j.time.Date`, `neo4j.time.Time`, `neo4j.time.DateTime`, `neo4j.time.Duration`, and `neo4j.spatial.Point`
- Python standard-library temporal types: `datetime.date`, `datetime.time`, `datetime.datetime`, and `datetime.timedelta`

Lists are supported only when their items are of one of the following types:

- Python built-ins: `bool`, `int`, `float`, `str`, `bytes`, `bytearray`
- Neo4j temporal and spatial types: `neo4j.time.Date`, `neo4j.time.Time`, `neo4j.time.DateTime`, `neo4j.time.Duration`, and `neo4j.spatial.Point`
- Python standard-library temporal types: `datetime.date`, `datetime.time`, `datetime.datetime`, and `datetime.timedelta`

Note that `list`, `dict`, and `NoneType` are not valid list item types — nested lists and nested dicts must be handled by a `serializer_fn` when `serialize_nested` is enabled.

```python
def custom_serializer(val):
    return "serialized"


class Child(Node):
    name: str
    age: int

    # Both `Human` and `Child` are used as labels
    loomi_config = {
        "labels": {"Human", "Child"}
    }


# `Adult` is used as the only label
class Adult(Node):
    job: str


class FamilyRelation(Relationship):
    loves_child: bool = Field(default=True)

    # `IS_PARENT_OF` is used as the type, and `custom_serializer`
    # is called when serializing nested properties
    loomi_config = {
        "type": "IS_PARENT_OF",
        "serializer_fn": custom_serializer
    }


# `WORKS_AT` is the type for this relationship
class WorksAt(Relationship):
    ...
```

Models also support inheritance, with specific rules applying to configuration merging based on the model type. Class properties are merged in the same way as for normal Pydantic classes.

For `Node` models, all configuration keys defined in the **inheriting class** override existing inherited ones. The only exception is the `labels` key, as **labels are merged**:

```python
from loomi import Node


class Human(Node):
    name: str
    age: int


# This class's labels will be `{"Human", "Worker"}`
class Worker(Human):
    job: str
```

For `Relationship` models, all configuration keys are **always overridden** by the inheriting class:

```python
import datetime

from loomi import Relationship


class Knows(Relationship):
    knows_since: datetime.datetime


# This class's type will be `LOVES`
class Loves(Knows):
    very_much: bool
```

## Accessing entity metadata

All populated models expose both `element_id` and `id` properties, reflecting their values in the database:

> [!NOTE]
> When using Memgraph, `element_id` and `id` resolve to the same value. This is because of how Memgraph handles internal IDs.

```python
with client.session() as session:
    result = session.run(
        "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
    )

    models = result.values()

    # Prints the `element_id` from the database
    print(models[0][0].element_id)
```
