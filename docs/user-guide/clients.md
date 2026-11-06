# Client usage, modes, and configuration

Your client connects a Neo4j driver to Loomi's model registration and result transformation features. Choose `Client` for synchronous code, or `AsyncClient` for asynchronous code. If you have not tried Loomi yet, the [quickstart](../getting-started.md) is a friendly place to begin.

## Create a client

Start with a Neo4j driver, then pass it to the matching Loomi client. Register the models you want Loomi to recognize. Before opening a Loomi session or using a query builder, initialize the client.

```python
import neo4j
from loomi import Client, Node


class Person(Node):
    name: str


driver = neo4j.GraphDatabase.driver(
    "<uri>", auth=("<user>", "<password>")
)
client = Client(driver)
client.register(Person)
client.initialize()

try:
    with client.session() as session:
        people = session.run(
            "MATCH (person:Person) RETURN person"
        ).value()
        print(people)
finally:
    driver.close()
```

When you call `initialize()`, Loomi checks the connection and reads the server metadata it needs. The async setup follows the same steps. Await asynchronous operations and open the session with `async with`:

```python
import neo4j
from loomi import AsyncClient, Node


class Person(Node):
    name: str


async def main():
    driver = neo4j.AsyncGraphDatabase.driver(
        "<uri>", auth=("<user>", "<password>")
    )
    client = AsyncClient(driver)
    client.register(Person)

    try:
        await client.initialize()
        async with client.session() as session:
            result = await session.run("MATCH (person:Person) RETURN person")
            people = await result.value()
            print(people)
    finally:
        await driver.close()
```

Register each `Node` and `Relationship` model you want Loomi to hydrate from query results. The [model guide](./models.md) shows how to define models and set their database labels or relationship types.

> [!IMPORTANT]
> Call `initialize()` before you use `client.session()`, `client.query()`, `client.update()`, or `client.delete()`. Loomi needs the server metadata that initialization loads for these operations.

## Choose a session mode

By default, `client.session()` gives you a Loomi session. It wraps the driver session and turns returned database nodes and relationships into registered models. You can still use the driver's familiar session interface.

Sometimes you may need the original Neo4j session instead. Ask for native mode explicitly:

```python
with client.session(mode="native") as session:
    result = session.run("MATCH (person:Person) RETURN person")
    print(result.single())
```

Native mode returns the driver's session directly. Its results contain native Neo4j records and entities, so Loomi does not transform or track them.

The `AsyncClient` supports the same `mode` option and returns a native `neo4j.AsyncSession` when `mode="native"` is selected.

## Configure driver sessions

Any keyword arguments you pass to `client.session()` go to the driver's `session()` method. You can use driver options such as the database name:

```python
with client.session(database="neo4j") as session:
    people = session.run("MATCH (person:Person) RETURN person").value()
```

You can pass the same options to `AsyncClient.session()`.

## Handle unregistered entities

Loomi matches returned entities by their labels or relationship type. By default, `strict_transformations=True`. If a result contains an entity without a registered model, Loomi raises `SerializationError` instead of returning a mixture of models and native entities.

If you would rather leave unmatched entities as native Neo4j entities, set `strict_transformations=False`. Loomi will still transform entities with registered models:

```python
client = Client(driver, strict_transformations=False)
```

You can set this option on `AsyncClient` too. Your result handling should then be ready for both Loomi models and native driver entities.

## Check the detected server

During initialization, Loomi detects whether it is connected to Neo4j or Memgraph and reads the server version. After initialization, call `client.server_type()` to check the detected type. With `AsyncClient`, first await initialization, then call `async_client.server_type()`. Most of the time, you can leave server detection to Loomi. It already chooses the right metadata query.

Next, visit [Model usage and configuration](./models.md) to learn how Loomi matches models to returned entities. The guide to [sessions, transactions, and results](./sessions-transactions-and-results.md) covers result methods, explicit transactions, and async usage.
