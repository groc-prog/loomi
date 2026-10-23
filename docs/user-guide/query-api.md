# Query API

This section covers the Query API loomi provides to make writing common queries simpler and more streamlined.

## Client methods

> [!TIP]
> Make sure to read the [client documentation](./clients.md) before continuing.

Each client provides an API for the most common query operations, offering a simple but flexible interface. All of the following client methods are supported on both sync and async clients, with the same interface and return values.

### Querying models

Use the `query` method to query data for a given model. It always returns a `list[Model]` containing all returned results:

```python
# Models are fully typed as list[Adult]
models = client.query(Adult).execute()

# Prints, for example:
# [<Adult element_id='551' labels={'Adult'}>, ...]
print(models)
```

> [!NOTE]
> You can pass additional keyword parameters, which are forwarded to the session or transaction running the query.

By default, this opens a new session and runs the query in its context. Similar to the [change tracker](./change-tracker.md), you can also pass a transaction and control its execution yourself:

```python
with client.session() as session:
    with session.begin_transaction() as tx:
        models = client.query(Adult, tx).execute()

        # Prints, for example:
        # [<Adult element_id='551' labels={'Adult'}>, ...]
        print(models)
```

The API does more than just fetch all matching nodes. The `query` method also provides the following chainable methods, which can be called before `execute` to change how the query is built:

| Method           | Description                                                                              |
| :--------------- | :--------------------------------------------------------------------------------------- |
| `.where(...)`    | Pass [additional filters](#filter-api), which are translated into a `WHERE ...` clause.  |
| `.order_by(...)` | Order the results by appending an `ORDER BY ...` clause to the resulting query.          |
| `.limit(...)`    | Limit the number of returned results.                                                    |
| `.skip(...)`     | Skip _x_ entities when results are collected.                                            |
| `.project(...)`  | Project the result into a dictionary with the provided keys instead of a model instance. |

Many of these methods have multiple overloads, so each is covered with an example below.

#### `.where(...)` usage example

```python
from loomi.query_api.functions.comparison import greater_than

# Fetch only adults older than 20 (> 20).
# See the `Filter API` section for all available operators.
models = (
    client.query(Adult)
    .where(greater_than(Adult.age, 20))
    .execute()
)
```

#### `.order_by(...)` usage example

> [!NOTE]
> Defining an `OrderBy` is optional. If omitted, the database default is used, which may vary depending on the database.

```python
from loomi.query_api.constants import OrderBy

# Order all returned results by age in descending order.
# All of the following queries have the same effect.
models = (
    client.query(Adult)
    .order_by(Adult.age, OrderBy.DESC)
    .execute()
)

models = (
    client.query(Adult)
    .order_by("age", OrderBy.DESC)
    .execute()
)

models = (
    client.query(Adult)
    .order_by({Adult.age: OrderBy.DESC})
    .execute()
)

models = (
    client.query(Adult)
    .order_by({"age": OrderBy.DESC})
    .execute()
)
```

Calling `order_by` on the same field multiple times always uses the last value:

```python
from loomi.query_api.constants import OrderBy

# Orders by age in ascending order, since `OrderBy.ASC` was called
# after `OrderBy.DESC`
models = (
    client.query(Adult)
    .order_by(Adult.age, OrderBy.DESC)
    .order_by(Adult.age, OrderBy.ASC)
    .execute()
)
```

#### `.limit(...)` usage example

```python
# Returns at most 2 results
models = (
    client.query(Adult)
    .limit(2)
    .execute()
)
```

Calling `limit` multiple times always uses the last value:

```python
# Returns at most 10 results
models = (
    client.query(Adult)
    .limit(2)
    .limit(10)
    .execute()
)
```

#### `.skip(...)` usage example

```python
# Skips the first 2 results encountered
models = (
    client.query(Adult)
    .skip(2)
    .execute()
)
```

Calling `skip` multiple times always uses the last value:

```python
# Skips the first 10 results encountered
models = (
    client.query(Adult)
    .skip(2)
    .skip(10)
    .execute()
)
```

#### `.project(...)` usage example

> [!NOTE]
> Any model properties not part of the projection are omitted during serialization.

```python
# Projects all results into a list of dictionaries of the form
# {"my_custom_key": <entity age property>}
models = (
    client.query(Adult)
    .project({"age": "my_custom_key"})
    .execute()
)

# Prints, for example:
# [{'my_custom_key': 29}, ...]
print(models)
```

Calling `project` multiple times always uses the last value:

```python
# Projects all results into a list of dictionaries of the form
# {"second_key": <entity age property>, "foobar": <entity name property>}
models = (
    client.query(Adult)
    .project({"age": "first_key"})
    .project({"age": "second_key", "name": "foobar"})
    .execute()
)

# Prints, for example:
# [{'second_key': 29, 'foobar': 'Alex'}, ...]
print(models)
```

Properties that do not exist on the model are filled with `None`:

```python
# Projects all results into a list of dictionaries of the form
# {"second_key": <entity age property>, "foobar": <entity name property>, "nonevalue": None}
models = (
    client.query(Adult)
    .project({"age": "second_key", "name": "foobar", "idontexist": "nonevalue"})
    .execute()
)

# Prints, for example:
# [{'second_key': 29, 'foobar': 'Alex', 'nonevalue': None}, ...]
print(models)
```

### Deleting models

Use the `delete` method to delete entities of a given model. Like the [change tracker](./change-tracker.md), this method uses `DETACH DELETE` under the hood, so all relationships connected to a deleted node are also deleted.

```python
# Returns a special `DeleteResult` containing meta information about the
# affected entities
result = client.delete(Adult).execute()

# Prints, for example:
# DeleteResult(affected=<num-affected>, affected_ids=[(<element_id>, <id>), ...])
print(result)
```

> [!NOTE]
> You can pass additional keyword parameters, which are forwarded to the session or transaction running the query.

Like all other client methods, `delete` opens a new session and runs the query in its context. If needed, you can also pass a transaction and control its execution yourself:

```python
with client.session() as session:
    with session.begin_transaction() as tx:
        result = client.delete(Adult, tx).execute()

        # Prints, for example:
        # DeleteResult(affected=<num-affected>, affected_ids=[(<element_id>, <id>), ...])
        print(result)

        # Abort the deletion
        tx.rollback()
```

The `delete` method also offers chainable methods to further control how the query is built:

| Method        | Description                                                                             |
| :------------ | :-------------------------------------------------------------------------------------- |
| `.where(...)` | Pass [additional filters](#filter-api), which are translated into a `WHERE ...` clause. |

#### `.where(...)` usage example

```python
from loomi.query_api.functions.comparison import starts_with

# Delete only adults whose name starts with `A`.
# See the `Filter API` section for all available operators.
result = (
    client.delete(Adult)
    .where(starts_with(Adult.name, "A"))
    .execute()
)
```

### Updating models

Use the `update` method to set the properties of entities of a given model. This acts as a batch update of multiple properties, and updates based on a property's current value are also supported.

```python
# Returns a special `UpdateResult` containing meta information about the
# affected entities
result = client.update(Adult).set_(Adult.age, 26).execute()

# Prints, for example:
# UpdateResult(affected=<num-affected>, affected_ids=[(<element_id>, <id>), ...])
print(result)
```

> [!NOTE]
> You can pass additional keyword parameters, which are forwarded to the session or transaction running the query.

Like all other client methods, `update` opens a new session and runs the query in its context. If needed, you can also pass a transaction and control its execution yourself:

```python
with client.session() as session:
    with session.begin_transaction() as tx:
        result = client.update(Adult).set_(Adult.age, 26).execute()

        # Prints, for example:
        # UpdateResult(affected=<num-affected>, affected_ids=[(<element_id>, <id>), ...])
        print(result)

        # Abort the update before it is committed
        tx.rollback()
```

The `update` method also offers chainable methods to further control how the query is built:

| Method        | Description                                                                                                              |
| :------------ | :----------------------------------------------------------------------------------------------------------------------- |
| `.where(...)` | Pass [additional filters](#filter-api), which are translated into a `WHERE ...` clause.                                  |
| `.set_(...)`  | Define which properties are updated and to which values. Translates into a `SET <variable>.<property> = <value>` clause. |

#### `.where(...)` usage example

```python
from loomi.query_api.functions.comparison import starts_with

# Update the age of adults whose name starts with `A` to 26.
# See the `Filter API` section for all available operators.
result = (
    client.update(Adult)
    .where(starts_with(Adult.name, "A"))
    .set_(Adult.age, 26)
    .execute()
)
```

#### `.set_(...)` usage example

```python
# Update the age of all adults to 26
result = (
    client.update(Adult)
    .set_(Adult.age, 26)
    .execute()
)
```

Calling `set_` on the same property multiple times always uses the last value:

```python
# Updates the age of all adults to 30
result = (
    client.update(Adult)
    .set_(Adult.age, 26)
    .set_(Adult.age, 30)
    .execute()
)
```

You can also update properties based on their current values without loading them from the database first:

```python
from loomi.query_api.functions.transformation import to_upper

# Update the name of all adults to an uppercase version of their
# current value.
# See the `Filter API` section for all available database functions.
result = (
    client.update(Adult)
    .set_(Adult.name, to_upper(Adult.name))
    .execute()
)
```

## Filter API

The Filter API provides a large preset of operators, helpers, and database functions that are guaranteed to work on both Neo4j and Memgraph. Helpers are grouped by purpose:

- **Arithmetic**: Operators for numeric calculations (`add`, `subtract`, etc.).
- **Identity**: For referencing different types of IDs.
- **Comparison**: For comparing values (`equals`, `starts_with`, etc.), compound and logical operators (`and`, `not`, etc.), and writing custom expressions (`cypher`).
- **Collections**: For referencing nested paths or list paths (`all_`, `single`, etc.).
- **Transformation**: Database functions (`tail`, `abs_`, etc.) and custom database functions (`create_db_function`).

The sections below cover, in order: (1) how model paths and helpers compose, (2) the full helper catalog, (3) how to combine helpers with values, and (4) how to build your own helpers.

### Model paths and field descriptors

> [!TIP]
> Throughout this section, *field path* and *field descriptor* refer to the same thing: a property path on a model, such as `Adult.name`.

As you may have seen by now, loomi lets you reference model property paths in expressions. This works for different types of paths, with a few caveats:

- Union types may not resolve to their correct type when using type checkers such as Pylance.
- Properties typed as dictionaries do not support type inference for their values.

Beyond these, all common field paths are supported:

> [!CAUTION]
> Only Memgraph supports nested properties. loomi still builds the expression, but Neo4j will not be able to run it.

| Type                                  | Example                                       | Path                                                                    |
| :------------------------------------ | :-------------------------------------------- | :---------------------------------------------------------------------- |
| Top-level paths                       | `Adult.age`                                   | `v0.age`                                                                |
| Nested paths                          | `Adult.metadata.event.timestamp`              | `v0.metadata.event.timestamp`                                           |
| List paths with index                 | `Adult.events[0]`                             | `v0.events[0]`                                                          |
| Nested list paths with nested indexes | `Adult.events[0].timestamps[3].value`         | `v0.events[0].timestamps[3].value`                                      |
| List paths with item operator         | `any_(Adult.events)`                          | `ANY(v1 IN v0.events)`                                                  |
| Nested list paths with item operators | `single(any_(Adult.events).timestamps).value` | `ANY(v1 IN v0.events WHERE SINGLE(v2 IN v1.timestamps WHERE v2.value))` |

These paths also support most basic operators through Python's magic methods:

| Magic method   | Example           | Corresponding helper    |
| :------------- | :---------------- | :---------------------- |
| `__eq__`       | `Adult.age == 26` | `equals`                |
| `__ne__`       | `Adult.age != 26` | `not_equals`            |
| `__gt__`       | `Adult.age > 26`  | `greater_than`          |
| `__ge__`       | `Adult.age >= 26` | `greater_than_or_equal` |
| `__lt__`       | `Adult.age < 26`  | `less_than`             |
| `__le__`       | `Adult.age <= 26` | `less_than_or_equal`    |
| `__add__`      | `Adult.age + 5`   | `add`                   |
| `__radd__`     | `5 + Adult.age`   | `reflected_add`         |
| `__sub__`      | `Adult.age - 5`   | `subtract`              |
| `__rsub__`     | `5 - Adult.age`   | `reflected_subtract`    |
| `__mul__`      | `Adult.age * 5`   | `multiply`              |
| `__rmul__`     | `5 * Adult.age`   | `reflected_multiply`    |
| `__truediv__`  | `Adult.age / 5`   | `divide`                |
| `__rtruediv__` | `5 / Adult.age`   | `reflected_divide`      |
| `__mod__`      | `Adult.age % 5`   | `modulo`                |
| `__rmod__`     | `5 % Adult.age`   | `reflected_modulo`      |
| `__pow__`      | `Adult.age ** 5`  | `pow_`                  |
| `__rpow__`     | `5 ** Adult.age`  | `reflected_pow`         |

### Helper catalog

The helpers below are guaranteed to work on both Neo4j and Memgraph. Each group is documented in its own subsection.

#### Arithmetic helpers

Arithmetic helpers perform mathematical calculations and always involve either a field descriptor or a database function paired with a numeric value.

> [!TIP]
> These helper functions power the [field descriptor magic methods](#model-paths-and-field-descriptors) under the hood. There is no functional difference between using a helper function and its corresponding magic method on a model.

| Helper function      | Resulting query  |
| :------------------- | :--------------- |
| `add`                | `Adult.age + 5`  |
| `reflected_add`      | `5 + Adult.age`  |
| `subtract`           | `Adult.age - 5`  |
| `reflected_subtract` | `5 - Adult.age`  |
| `multiply`           | `Adult.age * 5`  |
| `reflected_multiply` | `5 * Adult.age`  |
| `divide`             | `Adult.age / 5`  |
| `reflected_divide`   | `5 / Adult.age`  |
| `modulo`             | `Adult.age % 5`  |
| `reflected_modulo`   | `5 % Adult.age`  |
| `pow_`               | `Adult.age ** 5` |
| `reflected_pow`      | `5 ** Adult.age` |

#### Identity helpers

Identity helpers are primarily used to reference different types of IDs in expressions.

> [!NOTE]
> loomi automatically detects when it is running against Memgraph and rewrites any use of element ID to ID.

| Helper function | Resulting query     |
| :-------------- | :------------------ |
| `element_id`    | `element_id(Adult)` |
| `id_`           | `id(Adult)`         |

#### Comparison helpers

Comparison helpers are a collection of operators used to compare either a field descriptor or a database function with another field descriptor, database function, or static value.

| Helper function         | Resulting query                          |
| :---------------------- | :--------------------------------------- |
| `equals`                | `Adult.age = 5`                          |
| `greater_than`          | `Adult.age > 5`                          |
| `greater_than_or_equal` | `Adult.age >= 5`                         |
| `less_than`             | `Adult.age < 5`                          |
| `less_than_or_equal`    | `Adult.age <= 5`                         |
| `is_null`               | `Adult.metadata IS NULL`                 |
| `is_not_null`           | `Adult.metadata IS NOT NULL`             |
| `in_`                   | `Adult.name IN ['Alex', 'Sam']`          |
| `starts_with`           | `Adult.name STARTS WITH 'A'`             |
| `ends_with`             | `Adult.name ENDS WITH 'x'`               |
| `contains`              | `Adult.name CONTAINS 'le'`               |
| `regex`                 | `Adult.name =~ '[aA]lex'`                |
| `cypher`                | Whatever expression you decide to build. |

#### Collection helpers

Collection helpers build different types of list paths.

| Helper function | Resulting query                  |
| :-------------- | :------------------------------- |
| `all_`          | `ALL(hobby IN Adult.hobbies)`    |
| `any_`          | `ANY(hobby IN Adult.hobbies)`    |
| `none`          | `NONE(hobby IN Adult.hobbies)`   |
| `single`        | `SINGLE(hobby IN Adult.hobbies)` |

#### Transformation helpers

Transformation helpers wrap database functions that accept a single value.

> [!CAUTION]
> Expressions nested inside database functions, such as `abs(a.age - b.age)`, are currently **not supported**.

> [!NOTE]
> loomi does not provide a built-in helper for every available database function. It only ships helpers for functions supported by both Neo4j and Memgraph. If you need a custom database function, see [Creating your own transformation helpers](#creating-your-own-transformation-helpers).

| Helper function | Resulting query        |
| :-------------- | :--------------------- |
| `tail`          | `tail(Adult.hobbies)`  |
| `abs_`          | `abs(Adult.net_worth)` |
| `ceil`          | `ceil(Adult.salary)`   |
| `floor`         | `floor(Adult.salary)`  |
| `round_`        | `round(Adult.salary)`  |
| `ltrim`         | `ltrim(Adult.name)`    |
| `rtrim`         | `rtrim(Adult.name)`    |
| `trim`          | `trim(Adult.name)`     |
| `to_lower`      | `toLower(Adult.name)`  |
| `to_upper`      | `toUpper(Adult.name)`  |

### Composing helpers

All built-in helpers accept either static values or other [transformation helpers](#transformation-helpers) as the value argument. This is especially useful for referencing a modified version of a property:

```python
# Static values
expression = equals(Adult.name, "Alex")

# Transformed static value
expression = equals(Adult.name, trim("Alex"))

# Transformed property
expression = equals(to_upper(Adult.name), "ALEX")

# Transformed properties, values, and nested transformations
expression = starts_with(to_lower(trim(Adult.name)), to_lower(trim("al")))
```

### Creating your own transformation helpers

Since loomi does not support every available database function in Neo4j and Memgraph, and some functions (such as `round`) do not accept all parameters on both databases, you can define your own with `create_db_function`.

Database functions are created by defining a string template that is used when compiling a query. The template may contain the following placeholders, some of which are optional:

- **`variable_or_parameter`**: Replaced with the variable and full property path (e.g., `v0.name`). You can also pass only the model, without any path, to use just the variable.
- **`arg<num>`**: An arbitrary number of placeholders named `arg<num>`, where `num` is the index of the argument passed to the helper.

The following examples show a few custom database function implementations:

```python
substring_db_func = create_db_function(
    "substring({variable_or_parameter}, {arg0}, {arg1})"
)

# Builds a query like `substring(v0.name, 0, 2) = $p0`
equals(substring_db_func(Adult.name, 0, 2), "Al")


labels_db_func = create_db_function(
    "labels({variable_or_parameter})"
)

# Builds a query like `labels(v0) = $p0`
equals(labels_db_func(Adult), ["Adult"])
```
