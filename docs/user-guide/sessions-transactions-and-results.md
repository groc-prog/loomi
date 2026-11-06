# Sessions, transactions, and results

Loomi wraps Neo4j sessions and transactions so you can keep the driver's familiar workflow and also receive graph entities as models. Use `Client` and `Session` in synchronous code. For asynchronous code, use `AsyncClient` and `AsyncSession`.

## Run Cypher in a session

By default, `client.session()` gives you a Loomi session. You can run Cypher just as you do with the Neo4j driver. Pass values as parameters instead of formatting them into the query string:

```python
with client.session() as session:
    result = session.run(
        "MATCH (person:Person {name: $name}) RETURN person",
        {"name": "Ada"},
    )
    person = result.value()[0]
```

When a returned node or relationship matches a model registered with the client, Loomi converts it to that model. Primitive values and other non-entity results stay as they are. By default, Loomi raises `SerializationError` if an entity has no registered model. The [client guide](./clients.md) explains how to allow native entities and when to use a native session.

The async session works the same way. Remember to await its operations:

```python
async with async_client.session() as session:
    result = await session.run(
        "MATCH (person:Person {name: $name}) RETURN person",
        {"name": "Ada"},
    )
    people = await result.values()
    person = people[0][0]
```

## Consume results

Loomi transforms entities returned by the result methods. Here are a few you will likely use often:

- `single()` to consume one record
- `values()` to collect result columns as rows
- `value()` to collect values from one column
- iteration or `fetch(n)` to consume records
- `to_eager_result()` to consume the result eagerly
- `graph()` to get a graph containing transformed entities.

These methods follow the behavior of the underlying driver. In async code, await result methods and use `async for` to iterate:

```python
async with async_client.session() as session:
    result = await session.run("MATCH (person:Person) RETURN person")
    record = await result.single()

    result = await session.run("MATCH (person:Person) RETURN person")
    async for record in result:
        print(record["person"])
```

Call a result's `graph()` method to get a Loomi `Graph`. Its `nodes` and `relationships` collections contain transformed entities when you have registered matching models. If your query returns a path, Loomi gives you a `Path` with `nodes`, `relationships`, `start_node`, `end_node`, and `graph` accessors.

## Use an explicit transaction

Use an explicit transaction when you want several queries to share a commit or rollback boundary. Start it from a Loomi session. Its wrapper also transforms returned entities.

```python
with client.session() as session:
    transaction = session.begin_transaction()
    try:
        transaction.run(
            "CREATE (:Person {name: $name})",
            {"name": "Ada"},
        )
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
```

Here is the same flow with an async client. Await transaction creation, query execution, and commit or rollback:

```python
async with async_client.session() as session:
    transaction = await session.begin_transaction()
    try:
        await transaction.run(
            "CREATE (:Person {name: $name})",
            {"name": "Ada"},
        )
        await transaction.commit()
    except Exception:
        await transaction.rollback()
        raise
```

Follow the driver's documentation for transaction lifecycle and error handling. Loomi sessions also expose other driver methods, but Loomi transforms results from its wrapped `run()` method. Use that method when you want models in returned records.

## Enable change tracking

You can also opt in to change tracking by passing `tracking=True` to `session.run()` or `transaction.run()`. Loomi adds returned registered entities to that wrapper's tracker. The [change tracker guide](./change-tracker.md) shows how to review and flush those changes.
