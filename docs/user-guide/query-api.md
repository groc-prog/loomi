# Query API

The Query API helps you build common Cypher queries from registered model fields. You get typed field references, and Loomi passes ordinary values as query parameters for you. The examples here assume you have defined and registered your models and initialized the client. If you have not done that yet, start with [Models](./models.md) and [Clients](./clients.md).

You can import Query API helpers from their modules under `loomi.query_api.functions`. They are not all available directly from `loomi`.

## Query nodes and relationships

Pass a `Node` or `Relationship` model to `client.query()`, then use its field descriptors to build filters. Loomi passes ordinary Python values in expressions as query parameters.

```python
from loomi.query_api.functions.comparison import ends_with, greater_than

adults = (
    client.query(Adult)
    .where(greater_than(Adult.age, 18))
    .where(ends_with(Adult.name, "Smith"))
    .execute()
)
```

When you call `.where()` more than once, Loomi joins the filters with `AND`. To combine conditions with `OR`, `AND`, or negation, use the helpers:

```python
from loomi.query_api.functions.comparison import ends_with, or_, starts_with

adults = client.query(Adult).where(
    or_(starts_with(Adult.name, "Ada"), ends_with(Adult.name, "Lovelace"))
).execute()
```

You can also compare field descriptors with `==`, `!=`, `>`, `>=`, `<`, and `<=`. For compound conditions, use `&`, `|`, or `~` instead of Python's `and` and `or`. Be sure to put parentheses around each comparison:

```python
adults = client.query(Adult).where(
    (Adult.age >= 18) & (Adult.name != "")
).execute()
```

If you prefer, write compound conditions with `and_()`, `or_()`, and `not_()`. The `loomi.query_api.functions.comparison` module also includes `equals`, `not_equals`, `greater_than`, `less_than`, `starts_with`, `ends_with`, `contains`, `regex`, `in_`, `is_null`, and `is_not_null`.

## Order, limit, skip, and project

Use `order_by()` with a model field descriptor or field name. Choose `OrderBy.ASC` or `OrderBy.DESC` to set the direction. You can also use `skip()` and `limit()` to page through results.

```python
from loomi.query_api.constants import OrderBy

adults = (
    client.query(Adult)
    .where(Adult.age >= 18)
    .order_by(Adult.name, OrderBy.ASC)
    .skip(10)
    .limit(10)
    .execute()
)
```

Use `project()` when you only need selected properties. You can pass a mapping from model fields to result keys, or use a Pydantic model to describe the fields you want.

```python
names = client.query(Adult).project({Adult.name: "name"}).execute()
```

The mapping form returns dictionaries. If you use a Pydantic projection, give it fields with names that match the projected properties:

```python
from pydantic import BaseModel


class AdultSummary(BaseModel):
    name: str
    age: int


summaries = client.query(Adult).project(AdultSummary).execute()
```

You can query relationship models with the same builder. For example, `client.query(HasChild).where(HasChild.since >= 2020).execute()` finds relationships from 2020 onward.

## Update and delete

Use `client.update(Model)` to match models and change their properties. You need to call `.set()` at least once. Loomi parameterizes values for you. You can also set a property to a field descriptor or supported expression.

```python
updated = (
    client.update(Adult)
    .where(Adult.name == "Ada")
    .set(Adult.age, 37)
    .execute()
)

print(updated.affected)
print(updated.affected_ids)
```

`UpdateResult.affected` tells you how many entities were changed. The `affected_ids` list contains an `(element_id, id)` pair for each one. You can delete matching entities with `client.delete(Model)`, followed by `.where(...).execute()`. It returns a `DeleteResult` with the same fields.

> [!WARNING]
> Deleting a node uses Cypher `DETACH DELETE`, which also deletes relationships connected to that node. Deleting a relationship model deletes only matching relationships.

You can pass a transaction to a builder to run the query inside it. If you do not provide one, the client opens a session for the operation. For example, call `client.update(Adult, transaction=tx).where(...).set(...).execute()`.

With an async client, the builder works the same way. Just remember to await `execute()`:

```python
adults = await async_client.query(Adult).where(Adult.age >= 18).execute()
updated = await async_client.update(Adult).where(
    Adult.name == "Ada"
).set(Adult.age, 37).execute()
```

## Nested properties and list fields

Descriptors can follow nested Pydantic model fields and dictionary keys. If your model has an `address` field, for example, `Person.address.city` refers to its `city` property. You can also use `field[index]` with list and dictionary fields.

When you refer to an item in a list field without choosing a quantifier, Loomi uses `ANY`. To be more specific, import `all_`, `any_`, `none`, or `single` from `loomi.query_api.functions.collection`:

```python
from loomi.query_api.functions.collection import all_, any_, none

# Given Group.members: list[Person] and Person.age:
adults = client.query(Group).where(any_(Group.members).age >= 18).execute()
all_adults = client.query(Group).where(all_(Group.members).age >= 18).execute()
no_children = client.query(Group).where(none(Group.members).age < 18).execute()
```

The item model defines the nested fields in these examples. The quantifiers map to Cypher's `ANY`, `ALL`, `NONE`, and `SINGLE` list predicates.

## Arithmetic, database functions, and entity IDs

You can use arithmetic operators with numeric field descriptors. Supported operators include `+`, `-`, `*`, `/`, `%`, and `**`. Loomi compiles `**` as Cypher's `^`. Use these expressions in comparisons or when setting a value in an update. The corresponding helper functions live in `loomi.query_api.functions.arithmetic`.

The `loomi.query_api.functions.transformation` module includes database functions such as `abs_`, `ceil`, `floor`, `round_`, `trim`, `to_lower`, `to_upper`, and `tail`:

```python
from loomi.query_api.functions.transformation import to_lower
from loomi.query_api.functions.comparison import equals

people = client.query(Adult).where(
    equals(to_lower(Adult.name), "ada")
).execute()
```

If you need to filter by an entity identifier, use `element_id(Model)` or `id_(Model)` from `loomi.query_api.functions.identity`. Memgraph does not support Neo4j's `elementId` in the same way, so Loomi uses Memgraph's `id` expression instead.

## Custom Cypher expressions and database functions

If a built-in expression does not cover your predicate, use `cypher()` from `loomi.query_api.functions.comparison`. Loomi replaces model placeholders with query variables and binds parameter placeholders as query parameters. Leave off the `$` when you write a parameter placeholder name.

```python
from loomi.query_api.functions.comparison import cypher

people = client.query(Adult).where(
    cypher(
        "{person}.age % 2 = 0 AND {person}.age >= {minimum}",
        {"person": Adult},
        {"minimum": 18},
    )
).execute()
```

You can define a custom database function with `create_db_function()` from `loomi.query_api.functions.transformation`. Include `{variable_or_parameter}` in its template. For extra arguments, use placeholders such as `{arg0}` and `{arg1}`:

```python
from loomi.query_api.functions.transformation import create_db_function
from loomi.query_api.functions.comparison import greater_than

size = create_db_function("size({variable_or_parameter})")
long_names = client.query(Adult).where(
    greater_than(size(Adult.name), 3)
).execute()
```

Loomi inserts custom Cypher and database-function templates into generated queries. Only use templates you trust. Do not construct them by interpolating untrusted input. Keep data values in parameters, and use model fields for schema identifiers instead of joining in identifiers supplied by users.

For raw Cypher, transformed results, and explicit transactions, take a look at [Sessions, transactions, and results](./sessions-transactions-and-results.md).
