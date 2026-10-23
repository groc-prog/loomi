# Sessions, transactions, and results

This section covers how loomi clients expose sessions, transactions, and results for running queries.

## `native` mode vs. `loomi` mode

> [!NOTE]
> Both modes provide the same interface as the [`neo4j` package](https://pypi.org/project/neo4j/) for **sessions, transactions, and results**.

As mentioned elsewhere in this documentation, loomi is designed as a drop-in replacement for existing usage of drivers from the `neo4j` package. To achieve this, loomi clients share the same interface as drivers for running queries.

This means that in its simplest form, a loomi client can be **used in the same way as the neo4j driver** for running queries, with additional features enabled as you go:

> [!IMPORTANT]
> Clients only expose the interfaces needed to work with models. Other concerns, such as bookmarks, should be handled through the neo4j driver.

```python
client = Client(driver)
client.initialize()

# You can also pass any other session-related configuration here.
# `mode="native"` is what tells the client how results are returned.
with client.session(mode="native") as session:
    result = session.run(
        "CREATE (a:Adult $adult) RETURN a",
        {"adult": {"name": "John", "age": 28, "job": "Developer"}},
    )
    data = result.values()

    # Prints, for example:
    # [[<Node element_id='...' labels=frozenset({'Adult'}) properties={'name': 'John', 'job': 'Developer', 'age': 28}>]]
    print(data)
```

In **native mode**, the client performs no transformations or additional work: it returns the original session directly for you to work with. In **loomi mode**, on the other hand, all sessions, transactions, and results are **special wrappers** that still expose the **same interface as the originals**, with additional functionality such as an [attached change tracker](./change-tracker.md) or model transformation on result data access:

```python
# `loomi` is the default mode
with client.session() as session:
    # Query the database as you usually would.
    # You can also pass any session configuration as usual — everything
    # is forwarded to the original session object.
    result = session.run(
        "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
    )

    # `result` exposes the same interface as the original result, with some
    # extended functionality
    models = result.values()

    # Prints, for example:
    # [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
    print(models)
```

Transactions, like sessions, also provide a special wrapper that resolves models correctly when accessing the data from their results:

```python
with client.session() as session:
    tx = session.begin_transaction()

    # `result` is a special wrapper again
    result = tx.run(
        "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
    )
    models = result.values()

    # Prints, for example:
    # [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
    print(models)

    tx.commit()
```

## Passing configuration to underlying objects

If needed, you can also pass session and transaction configuration; the corresponding function call forwards them to the underlying original object automatically:

```python
# Pass session configuration
with client.session(database="neo4j", default_access_mode=neo4j.WRITE_ACCESS) as session:
    # Pass transaction configuration
    tx = session.begin_transaction(
        timeout=10.0,
        metadata={"application": "family_tree_loader", "triggered_by": "admin"}
    )

    result = tx.run(
        "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
    )
    models = result.values()

    # Prints, for example:
    # [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
    print(models)

    tx.commit()
```
