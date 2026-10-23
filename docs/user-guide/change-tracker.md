# Change tracker

This section covers how to use loomi's change tracker to automatically track changes to model entities.

## Session vs. transaction change trackers

Change trackers are always available on a session and its results, or on a transaction and its results.

By default, change tracking is disabled, and calling `flush` has no effect:

```python
with client.session() as session:
    session.run(
        "CREATE (a:Adult $adult)",
        {
            "adult": {"name": "John", "age": 28, "job": "Developer"},
        },
    )

    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    nodes[0][0].name = "Alex"
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    # Prints John
    print(nodes[0][0].name)
```

You can opt in by passing the `tracking` parameter when calling `run` on either a session or a transaction. This marks the returned data as tracked:

```python
with client.session() as session:
    session.run(
        "CREATE (a:Adult $adult)",
        {
            "adult": {"name": "John", "age": 28, "job": "Developer"},
        },
    )

    result = session.run("MATCH (a:Adult) RETURN a", tracking=True)
    nodes = result.values()

    nodes[0][0].name = "Alex"
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    # Prints Alex
    print(nodes[0][0].name)
```

When used this way, the change tracker opens a new transaction and runs all pending changes inside it. If you want full control over the transaction that runs the resulting queries, you can do that as well:

```python
with client.session() as session:
    session.run(
        "CREATE (a:Adult $adult)",
        {
            "adult": {"name": "John", "age": 28, "job": "Developer"},
        },
    )

    with session.begin_transaction() as tx:
        result = tx.run("MATCH (a:Adult) RETURN a", tracking=True)
        nodes = result.values()

        nodes[0][0].name = "Alex"
        tx.change_tracker.flush()

        result = tx.run("MATCH (a:Adult) RETURN a")
        nodes = result.values()

        # Prints Alex
        print(nodes[0][0].name)

        # Roll back the transaction containing the change tracker changes
        tx.rollback()

    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    # Still prints John because the transaction has not been committed
    print(nodes[0][0].name)
```

## Change tracker operation types

Change trackers can handle the most basic operations:

- **New entities:** Nodes or relationships that have not been persisted to the database yet. These are created when `flush` is called.
- **Changed entities:** Nodes or relationships that have been loaded from the database. These are updated when `flush` is called.
- **Deleted entities:** Nodes or relationships that have been marked for deletion. These are deleted from the database when `flush` is called.

Each change tracker object provides a number of methods for handling each operation.

### Saving and updating created entities

You can use the `add` method exposed by the change tracker to save new entities to the database when `flush` is called:

```python
with client.session() as session:
    john = Adult(name="John", age=28, job="Developer")
    session.change_tracker.add(john)
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    # Prints, for example:
    # [[<Adult element_id='551' labels={'Adult'}>]], containing only the 'John' node
    print(nodes)
    print(nodes[0][0].name)
```

You can also track relationships between nodes by passing the relationship, the start node, and the end node to the `add` method:

```python
with client.session() as session:
    john = Adult(name="John", age=28, job="Developer")
    kevin = Child(name="Kevin", age=2)
    is_parent_of = FamilyRelation(loves_child=True)
    session.change_tracker.add(is_parent_of, john, kevin)
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Child) RETURN a, r, c")
    entities = result.values()

    # Prints, for example:
    # [[<Adult element_id='552' labels={'Adult'}>, <FamilyRelation element_id='166' type='IS_PARENT_OF'>, <Child element_id='553' labels={'Child', 'Human'}>]]
    print(entities)
```

> [!NOTE]
> Properties of entities can still be changed after they have been added to the change tracker. You do **not** need to call `add` again after changing a property value.

Entities do not necessarily have to be fetched using the `tracking` flag to be tracked by the change tracker. You can also pass any entity fetched from the database to `add`, and any changes to its properties will be tracked automatically:

> [!WARNING]
> For property changes to be picked up by the change tracker, the properties must be updated **after the entity has been added** to the change tracker.

```python
with client.session() as session:
    session.run(
        "CREATE (a:Adult $adult)",
        {
            "adult": {"name": "John", "age": 28, "job": "Developer"},
        },
    )
    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    john = nodes[0][0]
    session.change_tracker.add(john)
    john.age = 40

    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    # Prints 40
    print(nodes[0][0].age)
```

You can even combine all of these examples into a single operation:

```python
with client.session() as session:
    session.run(
        "CREATE (a:Adult $adult), (c:Child $child)",
        {
            "adult": {"name": "John", "age": 28, "job": "Developer"},
            "child": {"name": "Kevin", "age": 2},
        },
    )

    result = session.run("MATCH (a:Adult), (c:Child) RETURN a, c")
    nodes = result.values()

    john = nodes[0][0]
    kevin = nodes[0][1]
    is_parent_of = FamilyRelation(loves_child=True)
    session.change_tracker.add(is_parent_of, john, kevin)

    john.age = 40
    kevin.age = 4
    is_parent_of.loves_child = False
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Child) RETURN a, r, c")
    entities = result.values()

    # Prints, for example:
    # [[<Adult element_id='561' labels={'Adult'}>, <FamilyRelation element_id='167' type='IS_PARENT_OF'>, <Child element_id='562' labels={'Child'}>]]
    print(entities)
    # Prints 40
    print(entities[0][0].age)
    # Prints False
    print(entities[0][1].loves_child)
    # Prints 4
    print(entities[0][2].age)
```

### Deleting entities

The `remove` method can be called with a node or a relationship to delete it from the database once `flush` is called. Queries generated by the change tracker always use `DETACH DELETE`, so any relationship attached to a removed node is also deleted automatically:

```python
with client.session() as session:
    session.run(
        "CREATE (a:Adult $adult)-[r:IS_PARENT_OF $relation]->(c:Child $child)",
        {
            "adult": {"name": "John", "age": 28, "job": "Developer"},
            "child": {"name": "Kevin", "age": 2},
            "relation": {"loves_child": True}
        },
    )
    result = session.run("MATCH (a:Adult) RETURN a")
    nodes = result.values()

    john = nodes[0][0]
    session.change_tracker.remove(john)
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult)-[r:IS_PARENT_OF]->(c:Child) RETURN a, c, r")
    nodes = result.values()

    # Prints []
    print(nodes)

    result = session.run("MATCH (c:Child) RETURN c")
    nodes = result.values()

    # Prints, for example:
    # [[<Child element_id='583' labels={'Child'}>]]
    print(nodes)
```

`remove` can also be used to remove unsaved entities from the change tracker after they have been added but before they are flushed:

```python
with client.session() as session:
    john = Adult(name="John", age=28, job="Developer")
    session.change_tracker.add(john)
    session.change_tracker.remove(john)
    session.change_tracker.flush()

    result = session.run("MATCH (a:Adult) RETURN a")
    entities = result.values()

    # Prints [] because John has never been saved
    print(entities)
```

### Clearing the change tracker

You can clear all entities from the change tracker, regardless of operation type:

```python
with client.session() as session:
    john = Adult(name="John", age=28, job="Developer")
    session.change_tracker.add(john)
    session.change_tracker.clear()

    # No query will be run
    session.change_tracker.flush()
```
