# Model usage & configuration

This section covers how `loomi` models are defined and configured for later usage in [queries](./sessions-transactions-and-results.md).

---

## Types of models

`loomi` has multiple types of models, some of which are defined by the user, while others are only returned by queries and **should never needed to be initialized by yourself**:

- `Node`: Represents a type of node in the database.
- `Relationship`: Represents a type of relationship in the database.
- `Graph`: A wrapper around the `neo4j.graph.Graph` class which provides correct typing and logic for working with loomi nodes and relationships. It provides **the same interface** as the `Graph` class from the `neo4j.graph` module.
- `Path`: A wrapper around the `neo4j.graph.Path` class which provides correct typing and logic for working with loomi nodes and relationships. It provides **the same interface** as the `Path` class from the `neo4j.graph` module.

---

## Defining your models

Under the hood, nodes and relationships are just [Pydantic classes](https://pydantic.dev/). If you have previously worked with Pydantic, you will get familiar with the way `loomi` makes use of Pydantics capabilities pretty quickly:

```python
# Nodes and relationships are defined as normal classes
# Any properties are translated to database entity properties
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

Models also support inheritance, with some specific rules applying to configuration merging based on the model type. Class properties are merged in the same way as for normal Pydantic classes.

For `Node` models, all configuration keys defined in the **inheriting class** will be overridden. The only exception to this rule is the `labels` key, as **labels are merged**:

```python
class Human(Node):
  name: str
  age: int


# This classes labels will be `{"Human", "Worker"}`
class Worker(Human):
  name: str
  age: int
  job: str
```

For `Relationship` models, all configuration keys are **always overridden**:

```python
class Knows(Relationship):
  knows_since: datetime.datetime


# This classes type will be `LOVES`
class Loves(Knows):
  very_much: bool
```


### Configuring models

As you might have seen in the [Getting started](../getting-started.md) docs, both nodes and relationships can be configured to behave differently. There are also some shared configuration options which affect both types of models:

> [!WARNING]
> When using custom (de)serializer functions, ensure your serialization logic is performant, as this can quickly become a performance trap when used heavily. In most cases, you should _consider switching to Memgraph_ when you make heavy use of nested properties.

> [!WARNING]
> Uniqueness of nodes labels and relationship types is not checked. The client will use the last model with matching labels/type when transforming results into models.

- **`serializer_fn`**: Only relevant when using both Neo4j and enabling `serialize_nested` on the client. By using this you can control how nested properties are serialized before they are stored. This function will be called for all fields which are not of a **supported data type** after `model.model_dump()` has been called. By default, `json.dumps` is used.
- **`deserializer_fn`**: Only relevant when using both Neo4j and enabling `serialize_nested` on the client. By using this you can control how nested properties are deserialized after they are loaded from the database. This function will be called for all fields where the data type does not match their annotation on the model. For lists, this will be called for each list item. By default, `json.dumps` is used.
- **`labels`**: Specific to **nodes**. This defines the labels used when the model is persisted to the database. By default, the **unchanged class name** is used as the only label.
- **`type`**: Specific to **relationships**. This defines the type used when the model is persisted to the database. By default, the **class name** converted into **SCREAMING_SNAKE_CASE** is used as the type.

> [!NOTE]
> Configuration options are always per model type and can not be defined globally.

```python
class Child(Node):
  name: str
  age: int

  # Define how the entity is displayed in the database
  loomi_config = {
    "labels": {"Human", "Child"}
  }


# `Adult` will be used as the only label
class Adult(Node):
  name: str
  age: int
  job: str


class FamilyRelation(Relationship):
  loves_child: bool = Field(default=True)

  loomi_config = {
    "type": "IS_PARENT_OF"
  }


# `WORKS_AT` will be the type for this relationship
class WorksAt(Relationship):
  ...
```


## Accessing entity metadata

All populated models expose both `element_id` and `id` properties which reflect their value in the database:

> [!NOTE]
> When using Memgraph, `element_id` and `id` will resolve to the same value. This is due to how Memgraph handles internal ID's.

```python
with client.session() as session:
  result = session.run(
    "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
  )

  models = result.values()

  # Prints the `element_id` from the database
  print(models[0].element_id)
```
