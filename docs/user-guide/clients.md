# Client usage, modes & configurations

This section covers how `loomi` wraps **neo4j drivers**, what modes they support and how they can be used and configured.


## How clients work

Since `loomi` uses the [`neo4j package`](https://pypi.org/project/neo4j/), all database interactions are handed off to the neo4j driver. Naturally, this means this package only builds on top of said driver, enhancing features and simplifying common tasks of a ORM.

To achieve this, `loomi` needs something to work with. Each time you want to create a new **loomi client**, you **have to pass a neo4j driver** to be used:

```python
# Create a driver to use or use a existing one
driver = neo4j.GraphDatabase.driver(
  uri="<uri>", auth=("<user>", "<password>")
)

client = Client(driver)
```

> [!IMPORTANT]
> Any driver configuration needs to be passed to the driver class when it is created. `loomi` does not provide any interface for defining driver configuration.

But before you can actually use any client you create, you have to **initialize it**. During initialization, the client will verify connectivity, fetch required metadata and initialize internal state:

```python
driver = neo4j.GraphDatabase.driver(
  uri="<uri>", auth=("<user>", "<password>")
)

client = Client(driver)
# The client has to be initialized before it is used!
client.initialize()
```

> [!NOTE]
> Attempting to run any action which requires a active database connection without previously initializing the client will result in a `ClientError`.


## Client types & configuration

### Synchronous vs. asynchronous clients

Similar to the [`neo4j package`](https://pypi.org/project/neo4j/), `loomi` also supports different client types:

- `Client`: A **synchronous** client which requires a `neo4j.Driver` instance.
- `AsyncClient`: A **asynchronous** client which requires a `neo4j.AsyncDriver` instance.

Both client types provide the same interface and configuration options.


### Configuration options

Both clients provide a few configuration options which can affect how to client handles it's data:

- **`serialize_nested`**: `loomi` supports both Neo4j and Memgraph. Since Neo4j does not support nested properties, but Memgraph does, this option allows you to store nested properties in Neo4j even with this limitation. But keep in mind that this comes with some other limitations like not being able to query these nested properties like you would in Memgraph. It is generally _not recommended_ to use this option.
- **`strict_transformations`**: During data fetching, clients attempt to parse the received data into their corresponding models. By default, serialization will fail if said model has not been registered with the client. Optionally, this can be changed to leave the data unchanged, meaning the client will just pass it on to the result without changing it.


## Registering models

On it's own the client is not much more than a fancy wrapper. It's real use-case is the transformation of data from a query into their corresponding models.

For the client to be able to transform query results, you have to register the models you want to work with with your client:

```python
# The full documentation for models can be found at `./models.md`
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
