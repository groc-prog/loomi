# Models

Models in loomi are just [`Pydantic`](https://pydantic.dev/docs/) models under the hood. This means everything you can do with Pydantic's models can also be done with loomi's models. From validation, to serialization and even more.


## Defining models

Models are defined in the exact same way as you would normally while using Pydantic, with the exception that you inherit from either the `Node` or `Relationship` class instead of `BaseModel`. As a example, a simple model like this:
```python
class Adult(BaseModel):
  name: str
  age: int
  job: str
```

can easily be converted to a loomi model:
```python
class Adult(Node):
  name: str
  age: int
  job: str
```

You can even inherit from other Pydantic models:
```python
class AdultModel(BaseModel):
  name: str
  age: int
  job: str


class Adult(Node, AdultModel): ...
```

Nested properties are also supported, with some [limitations](#limitations):
```python
class AdultMetadata(BaseModel):
  job: str
  married: bool


class Adult(Node):
  name: str
  age: int
  metadata: AdultMetadata
```


### Build-in Cypher types

> [!NOTE] Due to the way Pydantic works under the hood, not all Cypher types are supported.

Some data types, like spacial and temporal types, have a specific data type which is used by Neo4j and Memgraph to store them. A subset of these can also be defined on a model directly, telling the model to keep them as the defined data type during serialization. The supported types include:
- **Neo4jTemporalDateAnnotation**: Maps a Python date object to `neo4j.time.Date`.
- **Neo4jTemporalTimeAnnotation**: Maps a Python time object to `neo4j.time.Time`.
- **Neo4jTemporalDateTimeAnnotation**: Maps a Python datetime object to `neo4j.time.DateTime`.

You can use these special data types by annotating the type of a field with them:
```python
class Human(Node):
  birthday: Neo4jTemporalDate
```

If you have already existing models or can't change the data type already assigned to it, these special data types also expose a `.coerce()` method which allows you to use `Annotated` with them:
```python
class Human(Node):
  birthday: Annotated[datetime.date, BeforeValidator(Neo4jTemporalDateAnnotation.coerce)]
```


### Build-in properties

All models have some build-in properties which reflect some metadata from their corresponding database entities:
- **id:** Reflects the `id` of the given entity.
- **element_id:** Reflects the `elementId` of the given entity. This value is the same as `id` when connected to a **Memgraph instance**.

These values will be `None` until the models are hydrated, meaning this value will be set automatically when the client serialized a query result into a model.


### Defining model metadata

Nodes and relationships are identified by their labels and types. Similarly, loomi uses labels and relationships to identify which entity should be serialized into which model. But for this to work, it is important that **each registered model** has **unique labels or types**.

By default, labels and types are inferred by the class name, meaning a class named `Human` will have a single label named `Human` as well. It works the same for relationships, so a class named `Knows` will have a type called `KNOWS` (transformed to upper-case).

Of course, these names might not always be best suited for every use case. Due to this, loomi allows you to customize which labels and types are mapped to which models and entities. For this, you need to define the assigned labels or types directly on the model itself:

```python
class Child(Node):
  loomi_config = {
    "labels": {"Human", "Child"}
  }

class FamilyRelation(Relationship):
  loomi_config = {
    "type": "IS_PARENT_OF"
  }
```

There are also other settings which you can manage through the `loomi_config` class variable:
- **serializer_fn:** Determines which serialization function is used when serializing nested objects before storing them. Defaults to `json.dumps`. See [`Limitations`](#limitations) for more info.
- **deserializer_fn:** Determines which serialization function is used when de-serializing database values before serializing them into a model. Defaults to `json.loads`. See [`Limitations`](#limitations) for more info.


## Special graph models

The neo4j driver is not only limited to nodes and relationships. You can also get `Graph` or `Path` objects, which themselves contain nodes and relationships. For this to work seamlessly, loomi provides special `Graph` and `Path` classes which provide the same interface as the ones shipped with the neo4j package, with the only difference being that any nodes and relationships found in these objects are transformed by the client beforehand.


## Limitations

Like mentioned before, there are some limitations which come with the use of Pydantic for model serialization and validation.


### Unsupported Cypher types

There is currently no way to implement the remaining Cypher data types (points, duration, etc) due to the way Pydantic serializes these classes from the neo4j package into base data types.

When Pydantic encounters a class which inherits from a base type, it always tries to serialize that class to it's base type. This conflicts with the way serialization is currently implemented before passing the data to the neo4j driver.

> [!NOTE] A [Github issue](https://github.com/pydantic/pydantic/issues/11287) has been opened regarding this behavior.


### Nested properties when working with Neo4j

Neo4j does not allow nested properties natively, but Memgraph does. To add a additional layer of compatibility and to cover additional use cases, loomi attempts to serialize any nested properties into a serialized string. By default, a JSON-serialized string is used, but this behavior can be customized.

One thing to note when using a custom (de)serialization method is that the resulting **value must still be a valid data type** for the neo4j driver to process.


### Changing labels or types

Loomi does currently not have any build in migrations, meaning any changes in labels or types have to be accounted for by you, the developer. If not managed carefully, the client will no longer be able to map the labels/types of entities to the correct models, resulting in unexpected results from queries.
