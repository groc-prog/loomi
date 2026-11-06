# Model usage and configuration

Loomi models describe the properties and database identity of your graph's nodes and relationships. They are Pydantic models, so you get typed fields, defaults, validation, and familiar serialization methods along with Loomi's graph features.

## Define node and relationship models

To model a node, subclass `Node`. For a relationship, subclass `Relationship`. Add type annotations for the database properties. By default, a node uses its class name as its label. Loomi turns a relationship class name into an uppercase snake case type.

```python
from pydantic import Field
from loomi import Node, Relationship


class Adult(Node):
    name: str
    age: int
    job: str


class Child(Node):
    name: str
    age: int
    loomi_config = {"labels": {"Human", "Child"}}


class HasChild(Relationship):
    since: int
    is_guardian: bool = Field(default=True)
    loomi_config = {"type": "IS_PARENT_OF"}
```

In this example, `Adult` has the `Adult` label. `Child` has both `Human` and `Child`, and `HasChild` uses the relationship type `IS_PARENT_OF`. Make sure these names match the labels and type in your stored data and Cypher queries.

You can check a model's graph identity with these class methods:

```python
assert Adult.labels() == {"Adult"}
assert Child.labels() == {"Human", "Child"}
assert HasChild.type() == "IS_PARENT_OF"
```

## Configure labels and relationship types

Set `loomi_config` on a model class when you want to customize its graph identity:

- Nodes accept a set of `labels`.
- Relationships accept a `type` string.

Subclasses inherit configuration. Node labels are merged across the model hierarchy. A subclass can override relationship configuration. If you do not set an identity explicitly, Loomi uses the class name as described above.

When Loomi reads an entity, it looks for a model registered with the complete node label set or the relationship type. Register your models with the client before querying to have results converted to those model classes. The [client guide](./clients.md) walks you through registration.

## Validate and serialize properties

Pydantic checks field annotations when you create a model. Loomi also validates assignments, so you get a validation error if you assign a value with the wrong type or outside the field's constraints.

```python
child = Child(name="Holly", age=5)
child.age = 6

properties = child.model_dump()
print(properties)
```

Use Pydantic's `Field` to set defaults, add validation constraints, or provide aliases. Pydantic accepts aliases when it validates a model. Loomi also uses aliases when it serializes properties for storage.

```python
from pydantic import Field
from loomi import Node


class Person(Node):
    full_name: str = Field(alias="name")


person = Person(name="Ada Lovelace")
assert person.full_name == "Ada Lovelace"
```

## Database IDs and hydration

You do not define `id` or `element_id` as model fields. Loomi exposes them as computed properties. Both are `None` on a model you create directly in Python. When Loomi transforms a node or relationship returned by a query, it fills them from the database entity.

```python
child = Child(name="Holly", age=5)
assert child.id is None
assert child.element_id is None
```

With Memgraph, Loomi reports the same value for `id` and `element_id`. The [change tracker](./change-tracker.md) does not copy generated IDs back to the original models when you call `flush()`. Query the entity again to get a hydrated model with its database IDs.

## Use models with a client

Register the model types you want Loomi to use for returned entities. The [quickstart](../getting-started.md) takes you through a complete example. For more on result consumption and hydration, see [Sessions, transactions, and results](./sessions-transactions-and-results.md).
