# Clients

Like mentioned in the beginning, a loomi client is just a fancy wrapper around the driver from the [`neo4j`](https://pypi.org/project/neo4j/) package, meaning you always initialize a driver from the neo4j package before you can initialize a loomi client.

```python
# Initialize the driver like usual
driver = neo4j.AsyncGraphDatabase.driver(
  uri="bolt://localhost:7687", auth=("neo4j", "password")
)

# Tell the loomi client which driver to use
client = AsyncClient(driver)
```


## Sync vs. Async

This package, similar to the neo4j package, provides both a sync and async version of the client. Both share the same interfaces and functionality, with the only difference being that the async client requires usage of the `async` and `await` keywords.

```python
async_client = AsyncClient(
  neo4j.AsyncGraphDatabase.driver(
    uri="bolt://localhost:7687", auth=("neo4j", "password")
  )
)

sync_client = Client(
  neo4j.GraphDatabase.driver(
    uri="bolt://localhost:7687", auth=("neo4j", "password")
  )
)
```


## Using the client in noop mode

Loomi clients are designed to be a drop-in replacement. As such, you can use them like you would use the driver from the neo4j package. They share the same interfaces for queries data.

> [!NOTE] Loomi clients only expose the necessary interfaces to work with models. Other things like bookmarks should be controlled with the neo4j driver.

Under the hood, clients only wrap the session provided by the driver, and then add additional functionality to them. You can run in noop mode by defining the session mode when starting a new session:

```python
client = Client(
  neo4j.GraphDatabase.driver(
    uri="bolt://localhost:7687", auth=("neo4j", "password")
  )
)

# You can also pass any other session-related configuration here
with client.session(mode="native") as session:
  result = await session.run(
    "CREATE (a:Adult $adult) RETURN a",
    {"adult": {"name": "John", "age": 28, "job": "Developer"}},
  )
  data = await result.values()

  # [[<Node element_id='...' labels=frozenset({'Adult'}) properties={'name': 'John', 'job': 'Developer', 'age': 28}>]]
  print(data)
```


## Registering models

For the client to be able to serialize entities from queries into their corresponding models, any models which should be serializable must be registered with the client first. If the client encounters a entity which has not been registered, the entity will be returned as-is.

```python
class Human(Node): ...

with client.session(mode="native") as session:
  result = session.run("MATCH (h:Human), (n:NotDefined) RETURN h, n")
  data = result.values()

  # [[<Human element_id='...' labels=frozenset({'Human'}) properties={}>], [<Node element_id='...' labels=frozenset({'NotDefined'}) properties={}>]]
  print(data)
```


## Initializing clients

Before a client can be used, it has to be initialized. The client uses this to get metadata information from the server, including the server version, type and more. This information is later on used to correctly handle Cypher differences between Neo4j and Memgraph.


## Using sessions and transactions

Like mentioned previously, clients provide a similar interface to drivers. The same is also true for clients when using sessions and transactions:

```python
# Auto-committing sessions
with client.session() as session:
  session.run(...)

# Manual session management
session = client.session()
session.run(...)
session.close()

# Auto-committing transactions
with client.session() as session:
  with session.begin_transaction() as tx:
    tx.run(...)

# Manual transaction management
session = client.session()

tx = session.begin_transaction()
tx.run(...)
tx.commit()
tx.close()

session.close()
```

All methods called on the client provide the same interface as the driver does, meaning any configuration values passed to a session or transaction can also be passed in the same way when the loomi client is used.


### Query results

The `Result` object returned by a session or transaction in mode `loomi` is also a specialized version of the `Result` object returned by a regular session or transaction. This special class overrides the following methods so that it returns the transformed results:
- **\_\_aiter\_\_** and **\_\_iter\_\_**
- **\_\_anext\_\_** and **\_\_next\_\_**
- **peek**
- **fetch**
- **to_eager_result**
- **single**
- **values**
- **value**
- **graph**

These methods, once again, provide the same interface as the original, but they also handle the transformation of database entities to loomi models.


### Using the change tracker

Session and transaction objects also provide a `change_tracker` property. This can be used to automatically generate queries for any added, updated or deleted entities:

```python
# Assume these models have been fetched beforehand and already exist
# in the database
marvin = Human(name="Marvin", age=42)
olaf = Human(name="Olaf", age=87)

john = Human(name="John", age=21)
jane = Human(name="Jane", age=20)
knows_relationship = Knows()

with client.session() as session:

  # Adding new models to the change tracker
  # This can be omitted since the change tracker would also recognize
  # john because of the added relationship
  session.change_tracker.add(john)
  # Also works with relationships
  session.change_tracker.add(knowns_relationship, john, jane)

  # Updating existing (hydrated) models
  # This will become a noop if marvin does not have any changes
  session.change_tracker.add(marvin)

  # Delete existing (hydrated) models
  session.change_tracker.remove(olaf)

  # This is where the actual queries get generated and executed
  session.change_tracker.flush()
```

Each call to `.flush()` will open a new transaction for running any pending queries, ensuring other queries do not interfere. Any obsolete changes, like a new relationship which has it's start/end node removed before `.flush()` is called will be automatically omitted.

Since a transaction is used under the hood, we can also easily use the change tracker with a existing transaction:

```python
with client.session() as session:
  with session.begin_transaction() as tx:
    tx.change_tracker.add(...)
    tx.change_tracker.remove(...)

    tx.change_tracker.flush()
```

Behind the scenes, the generated queries are grouped together using a single `UNWIND <changes> MATCH <pattern> WHERE <identifiers> SET <properties>` query. This ensures there are no unnecessary round trips to the database.


## Query builders

> [!NOTE] The following examples make use of filter expressions. For everything which is supported by `.where()` filters, see the [Queries section](./Queries.md).

Loomi clients provide basic query builders for **fetching, updating and deleting models** without you having to write a single query.


### Fetching entities

Models for a specific entity can be easily fetched using the `.query()` method on the client. This method will return a query builder which provides a number of basic options for defining how the query should be executed:
- `.where()`: Allows you to filter which entities should be returned
- `.order_by()`: Orders the matched entities
- `.limit()`: Limits the number of matched entities
- `.skip()`: Skips the given amount of matched entities
- `.project()`: Transforms the matched entities in a dictionary with the given keys
- `.execute()`: Generates and runs the query

```python
query = client.query(Human)

# Only match humans who's name is "John"
# This is equal to a `WHERE e.name = 'John'` cypher query
query.where(Human.name == "John")

# Order all results by age in ascending order
query.order_by("age", OrderBy.ASC)

# Only get the first 10 results
query.limit(10)

# This actually generates and runs the query in a new session
# if no transaction is passed
results = query.execute()

# [[<Human element_id='...' labels=frozenset({'Human'}) properties={...}>], [<Human element_id='...' labels=frozenset({'Human'}) properties={...}>]]
print(results)
```

Optionally, you can also pass the transaction which should be used by the query:

```python
with client.session() as session:
  with session.begin_transaction() as tx:
    results = client.query(Human, tx).execute()

    # [[<Human element_id='...' labels=frozenset({'Human'}) properties={...}>], [<Human element_id='...' labels=frozenset({'Human'}) properties={...}>]]
    print(results)
```

### Batch updating entities

You can also do batch updates for multiple nodes. This is a more efficient way to update multiple models instead of using the change tracker since this allows you to update entities without fetching them first.

Similar to [fetching entities](#fetching-entities), you can also filter entities when updating them:

```python
query = client.update(Human)

# Only match humans who's name is "John"
# This is equal to a `WHERE e.age > 30` cypher query
query.where(Human.age > 30)

# Define the update which should be applied
# This will increment the `age` property for all Human nodes
# matched by the query by 2
query.set_(Human.age, Human.age + 2)

update_result = query.execute()

# UpdateResult(affected=<update-count>, affected_ids=[('<element-id>', <id>)])
print(update_result)
```

In contrast to the result when fetching models, this method returns a special `UpdateResult`, which contains the number of updated records and all of their **element IDs and IDs**.

This method also accepts a transaction which it will use to run the query, if a transaction is provided.

### Batch deleting entities

Besides fetching and updating, you can also delete multiple models with the same query builder style as the before mentioned. This shares the same interface as other query builder methods:

```python
query = client.delete(Human)

# Only match humans who's name is "John"
# This is equal to a `WHERE e.name STARTS WITH 'J'` cypher query
query.where(starts_with(Human.name, "J"))

delete_result = query.execute()

# DeleteResult(affected=<delete-count>, affected_ids=[('<element-id>', <id>)])
print(delete_result)
```

Just like the result for [batch updating entities](#batch-updating-entities), this method also returns a special `DeleteResult` which shares the same interface as the one returned when batch updating entities.
