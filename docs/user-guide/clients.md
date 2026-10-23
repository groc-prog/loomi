# Client usage, modes, and configuration

This section covers how loomi wraps **neo4j drivers**, which modes they support, and how they can be used and configured.

## How clients work

Because loomi builds on the [`neo4j` package](https://pypi.org/project/neo4j/), all database interactions are delegated to the underlying neo4j driver. loomi itself only adds features on top of that driver, enhancing functionality and simplifying common ORM tasks.

To do this, loomi needs a driver to work with. Each time you create a new **loomi client**, you **must pass a neo4j driver** for it to use:

```python
# Create a driver, or reuse an existing one
driver = neo4j.GraphDatabase.driver(
    uri="<uri>", auth=("<user>", "<password>")
)

client = Client(driver)
```

> [!IMPORTANT]
> Any driver configuration must be passed to the driver class when it is created. loomi does not provide any interface for defining driver configuration.

Before you can use a client, you have to **initialize it**. During initialization, the client verifies connectivity, fetches required metadata, and sets up its internal state:

```python
driver = neo4j.GraphDatabase.driver(
    uri="<uri>", auth=("<user>", "<password>")
)

client = Client(driver)
# The client must be initialized before use
client.initialize()
```

> [!NOTE]
> Attempting to run any action that requires an active database connection without first initializing the client will raise a `ClientError`.

## Client types and configuration

### Synchronous vs. asynchronous clients

Like the [`neo4j` package](https://pypi.org/project/neo4j/), loomi supports two client types:

- `Client`: a **synchronous** client that requires a `neo4j.Driver` instance.
- `AsyncClient`: an **asynchronous** client that requires a `neo4j.AsyncDriver` instance.

Both client types expose the same interface and configuration options.

### Configuration options

Both clients provide a few configuration options that affect how they handle their data:

- **`serialize_nested`**: loomi supports both Neo4j and Memgraph. Neo4j does not support nested properties, but Memgraph does. This option lets you store nested properties in Neo4j despite that limitation, but it comes with trade-offs — for example, you cannot query these nested properties the way you would in Memgraph. It is generally _not recommended_ to enable this option.
- **`strict_transformations`**: During data fetching, clients attempt to parse received data into the corresponding models. By default, parsing fails if the model has not been registered with the client. Optionally, this behavior can be changed so that unregistered data is left unchanged and passed straight through to the result.

## Registering models

On its own, a client is little more than a wrapper. Its real value is transforming query results into their corresponding models.

For the client to transform query results, you must register the models you want to work with:

```python
from pydantic import Field

# Full model documentation lives in ./models.md
class Child(Node):
    name: str
    age: int


class Adult(Node):
    name: str
    age: int
    job: str


class FamilyRelation(Relationship):
    loves_child: bool = Field(default=True)


driver = neo4j.GraphDatabase.driver(
    uri="<uri>", auth=("<user>", "<password>")
)

client = Client(driver)
client.register(Child, Adult, FamilyRelation)
```
