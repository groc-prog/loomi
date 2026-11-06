# Change tracker

The change tracker helps you save changes to node and relationship models without writing an update query for every property. You choose when to turn tracking on. Before you begin, make sure your models are registered and your client is initialized. The [model guide](./models.md) and [client guide](./clients.md) can help with that.

## Track entities returned from a query

Pass `tracking=True` to `run()` on a Loomi session or transaction. As you consume the result, Loomi adds registered nodes and relationships to that session or transaction's tracker. Update their properties, then call `flush()` to save your changes.

```python
with client.session() as session:
    result = session.run("MATCH (adult:Adult) RETURN adult", tracking=True)
    adults = result.value()

    adults[0].age += 1
    session.change_tracker.flush()
```

Tracking starts off disabled. Even without `tracking=True`, Loomi still turns matching entities into models. It just does not add them to the tracker automatically. You can always add a model yourself.

In async code, await `run()`, result methods, and `flush()`:

```python
async with async_client.session() as session:
    result = await session.run("MATCH (adult:Adult) RETURN adult", tracking=True)
    adults = await result.value()

    adults[0].age += 1
    await session.change_tracker.flush()
```

## Add, update, and delete models

Call `change_tracker.add(model)` to track an unsaved model for creation or a hydrated model for updates. When you track an existing model, call `add()` before changing its fields. The tracker records the current properties as its starting point, so it will not notice changes made earlier.

```python
with client.session() as session:
    adult = Adult(name="Ada", age=36, job="Engineer")
    session.change_tracker.add(adult)
    session.change_tracker.flush()
```

To update an existing entity, get a hydrated model from a Loomi query. Add it to the tracker before you edit it:

```python
with client.session() as session:
    adult = session.run("MATCH (adult:Adult) RETURN adult").value()[0]
    session.change_tracker.add(adult)
    adult.job = "Mathematician"
    session.change_tracker.flush()
```

Call `delete()` to mark a saved entity for removal. An unsaved entity is not in the database, so marking it for deletion has no effect there.

```python
with client.session() as session:
    adult = session.run("MATCH (adult:Adult) RETURN adult").value()[0]
    session.change_tracker.delete(adult)
    session.change_tracker.flush()
```

Deleting a node also removes its connected relationships from the database. If you want to stop tracking an entity without saving or deleting it, call `detach(model)`. Call `clear()` to discard all pending operations. Loomi clears the tracker after `flush()` too.

## Track relationships

To create a relationship, give the tracker the relationship model and both endpoint nodes. The nodes can be new models or hydrated models that already exist in the database.

```python
with client.session() as session:
    adult = Adult(name="Ada", age=36, job="Engineer")
    child = Child(name="Byron", age=8)
    relationship = HasChild(since=2024)

    session.change_tracker.add(relationship, adult, child)
    session.change_tracker.flush()
```

When the endpoints are new, the tracker creates them before creating the relationship. If either endpoint is missing, adding the new relationship raises `ChangeTrackerError`. You can also add an existing hydrated relationship to track its property changes, or mark it for deletion.

## Choose the transaction boundary

When you call `flush()` on a session tracker, Loomi opens a new transaction and commits it if the flush succeeds. A transaction tracker runs changes inside the transaction you already opened. It does not commit for you, so you decide whether to commit or roll back:

```python
with client.session() as session:
    with session.begin_transaction() as tx:
        adult = Adult(name="Ada", age=36, job="Engineer")
        tx.change_tracker.add(adult)
        tx.change_tracker.flush()
        tx.commit()
```

If you roll back, the flushed changes are rolled back with the transaction. Async trackers follow the same transaction rules. Just await `tracker.flush()` and the transaction operations.

## Re-query to get IDs for new models

The tracker uses generated database IDs when it creates related entities, but it does not copy those IDs back to your original unsaved models. After `flush()`, a newly added model still has `id` and `element_id` set to `None`. Query the entity again to get a hydrated model with its database IDs:

```python
with client.session() as session:
    adult = Adult(name="Ada", age=36, job="Engineer")
    session.change_tracker.add(adult)
    session.change_tracker.flush()

    saved_adult = session.run(
        "MATCH (adult:Adult {name: $name}) RETURN adult",
        {"name": "Ada"},
    ).value()[0]
    print(saved_adult.element_id)
```

The [sessions guide](./sessions-transactions-and-results.md) explains how to work with results. For query and update builders, continue to the [Query API guide](./query-api.md).
