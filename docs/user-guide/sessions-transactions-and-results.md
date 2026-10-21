# Sessions, transactions & results

This section covers how `loomi` clients expose sessions, transactions and results for running queries.


## `native` mode vs. `loomi` mode

> [!NOTE]
> Both modes provide the same interface as the [`neo4j package`](https://pypi.org/project/neo4j/) for **sessions, transactions and results**.

As mentioned in other parts of this documentation, `loomi` is designed to be a drop-in replacement for the existing usage of drivers from the `neo4j` package. To achieve this, clients share the same interface as drivers for running queries.

This means that in it's simplest form, a loomi client can be **used in the same way you would use the neo4j driver** for running your queries, enable additional features as you go:

> [!IMPORTANT]
> Clients only expose the necessary interfaces to work with models. Other things like bookmarks and others should be controlled with the neo4j driver.

```python
client = Client(driver)

# You can also pass any other session-related configuration here
# `mode="native"` is what tells the client how results are returned
with client.session(mode="native") as session:
  result = session.run(
    "CREATE (a:Adult $adult) RETURN a",
    {"adult": {"name": "John", "age": 28, "job": "Developer"}},
  )
  data = result.values()

  # [[<Node element_id='...' labels=frozenset({'Adult'}) properties={'name': 'John', 'job': 'Developer', 'age': 28}>]]
  print(data)
```

In **native mode**, the client will not perform any transformations or additional work, it will return the original session directly for you to work with. On the other hand, when using **loomi mode**, all sessions, transactions and results will be **special wrappers** which still expose the **same interface as the original**, with some additional functionality like a [attached change tracker](./change-tracker.md) or model transformation on result data access:

```python
# `loomi` is the default mode
with client.session() as session:
  # Query the database like you would usually
  # You can also pass any session configuration like you would usually, everything gets forwarded
  # to the original session object
  result = session.run(
    "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
  )

  # `result` provides the same interface as the original result with some extended functionality
  models = result.values()

  # Prints [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
  print(models)
```

Transactions, same as sessions, also provide a special wrapper which resolves models correctly when accessing the data from it's results:

```python
with client.session() as session:
  tx = session.begin_transaction()

  # `result` will be a special wrapper again
  result = tx.run(
    "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
  )
  models = result.values()

  # Prints [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
  print(models)

  tx.commit()
```


## Passing configuration to underlying objects

If you need to, you can also pass some session/transaction configurations and the corresponding function call will pass them to the underlying original object automatically:

```python
# Pass some session configuration
with client.session(database="neo4j", default_access_mode=neo4j.WRITE_ACCESS) as session:
  # Pass some transaction configuration
  tx = session.begin_transaction(
    timeout=10.0,
    metadata={"application": "family_tree_loader", "triggered_by": "admin"}
  )

  result = tx.run(
      "MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Human:Child) RETURN a, c"
  )
  models = result.values()

  # Prints [[<Adult element_id='...' labels={'Adult'}>, <Child element_id='...' labels={'Child', 'Human'}>]]
  print(models)

  tx.commit()
```
