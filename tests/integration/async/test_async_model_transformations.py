# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, cast

import neo4j
import neo4j.graph
import pytest
from pydantic import Field

from loomi._async.client import AsyncClient
from loomi.exceptions import SerializationError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from tests.conftest import DriverSpec


class TransformPerson(Node):
    name: str
    tags: list[str] = []
    payload: dict[str, Any] | None = None
    entries: list[dict[str, Any]] | None = None
    display_name: str = Field(alias="stored_name")

    loomi_config = {"labels": {"TransformPerson"}}


class TransformKnows(Relationship):
    metadata: dict[str, Any] | None = None
    history: list[dict[str, Any]] | None = None

    loomi_config = {"type": "TRANSFORM_KNOWS"}


class UnregisteredTransformNode(Node):
    name: str

    loomi_config = {"labels": {"UnregisteredTransformNode"}}


class UnregisteredTransformRelationship(Relationship):
    value: str

    loomi_config = {"type": "UNREGISTERED_TRANSFORM_RELATIONSHIP"}


def wrap_json(value: Any) -> str:
    return "wrapped:" + json.dumps(value)


def unwrap_json(value: str) -> Any:
    if not value.startswith("wrapped:"):
        raise ValueError("missing wrapped prefix")
    return json.loads(value.removeprefix("wrapped:"))


class CustomSerializedPerson(Node):
    name: str
    payload: dict[str, Any]
    events: list[dict[str, Any]]

    loomi_config = {
        "labels": {"CustomSerializedPerson"},
        "serializer_fn": wrap_json,
        "deserializer_fn": unwrap_json,
    }


class CustomSerializedKnows(Relationship):
    metadata: dict[str, Any]
    events: list[dict[str, Any]]

    loomi_config = {
        "type": "CUSTOM_SERIALIZED_KNOWS",
        "serializer_fn": wrap_json,
        "deserializer_fn": unwrap_json,
    }


class MissingSerializerPerson(Node):
    name: str
    payload: dict[str, Any]

    loomi_config = {"labels": {"MissingSerializerPerson"}, "serializer_fn": None}  # type: ignore


class MissingDeserializerPerson(Node):
    name: str

    loomi_config = {"labels": {"MissingDeserializerPerson"}, "deserializer_fn": None}  # type: ignore


class FailingDeserializerPerson(Node):
    name: str
    payload: dict[str, Any]

    loomi_config = {
        "labels": {"FailingDeserializerPerson"},
        "deserializer_fn": lambda _value: (_ for _ in ()).throw(ValueError("invalid payload")),
    }


class FailingDeserializerListPerson(Node):
    name: str
    events: list[dict[str, Any]]

    loomi_config = {
        "labels": {"FailingDeserializerListPerson"},
        "deserializer_fn": lambda _value: (_ for _ in ()).throw(ValueError("invalid event")),
    }


class UnsupportedValuePerson(Node):
    name: str
    payload: Any

    loomi_config = {"labels": {"UnsupportedValuePerson"}}


class UnsupportedValueKnows(Relationship):
    payload: Any

    loomi_config = {"type": "UNSUPPORTED_VALUE_KNOWS"}


class FailingListSerializerPerson(Node):
    name: str
    events: list[dict[str, Any]]

    loomi_config = {
        "labels": {"FailingListSerializerPerson"},
        "serializer_fn": lambda _value: (_ for _ in ()).throw(ValueError("serialize item")),
    }


class FailingListSerializerKnows(Relationship):
    events: list[dict[str, Any]]

    loomi_config = {
        "type": "FAILING_LIST_SERIALIZER_KNOWS",
        "serializer_fn": lambda _value: (_ for _ in ()).throw(ValueError("serialize item")),
    }


@pytest.fixture
async def transform_client(async_driver):
    client = AsyncClient(async_driver, serialize_nested=True)
    await client.initialize()
    client.register(TransformPerson, TransformKnows)
    return client


async def create_transform_graph(async_driver, driver_spec: DriverSpec) -> None:
    async with async_driver.session() as session:
        if driver_spec.name.value == "Neo4j":
            await session.run(
                """
                CREATE (alice:TransformPerson {
                    name: 'Alice', stored_name: 'A. Example',
                    tags: ['alice'],
                    payload: '{"city":"Paris","score":7}',
                    entries: ['{"kind":"work","rank":1}', '{"kind":"play","rank":2}']
                })
                CREATE (bob:TransformPerson {
                    name: 'Bob', stored_name: 'B. Example',
                    tags: ['bob'],
                    payload: '{"city":"Rome","score":8}', entries: []
                })
                CREATE (alice)-[:TRANSFORM_KNOWS {
                    metadata: '{"since":2024,"source":"manual"}',
                    history: ['{"year":2024,"level":"first"}']
                }]->(bob)
                """
            )
        else:
            await session.run(
                """
                CREATE (alice:TransformPerson {
                    name: 'Alice', stored_name: 'A. Example',
                    tags: ['alice'],
                    payload: {city: 'Paris', score: 7},
                    entries: [{kind: 'work', rank: 1}, {kind: 'play', rank: 2}]
                })
                CREATE (bob:TransformPerson {
                    name: 'Bob', stored_name: 'B. Example',
                    tags: ['bob'],
                    payload: {city: 'Rome', score: 8}, entries: []
                })
                CREATE (alice)-[:TRANSFORM_KNOWS {
                    metadata: {since: 2024, source: 'manual'},
                    history: [{year: 2024, level: 'first'}]
                }]->(bob)
                """
            )


async def get_transform_graph_counts(async_driver) -> tuple[int, int]:
    async with async_driver.session() as session:
        nodes = await session.run("MATCH (person:TransformPerson) RETURN count(person) AS count")
        node_record = await nodes.single()
        relationships = await session.run(
            "MATCH ()-[relationship:TRANSFORM_KNOWS]->() RETURN count(relationship) AS count"
        )
        relationship_record = await relationships.single()

    assert node_record is not None
    assert relationship_record is not None
    return node_record["count"], relationship_record["count"]


class TestAsyncModelTransformation:
    async def test_registered_node_deserialization_maps_alias_and_skips_unknown_fields(
        self, async_driver, driver_spec: DriverSpec, transform_client
    ):
        await create_transform_graph(async_driver, driver_spec)

        people = await transform_client.query(TransformPerson).execute()

        assert {person.name for person in people} == {"Alice", "Bob"}
        alice = next(person for person in people if person.name == "Alice")
        assert alice.display_name == "A. Example"
        assert alice.tags == ["alice"]
        assert alice.payload == {"city": "Paris", "score": 7}
        assert alice.entries == [{"kind": "work", "rank": 1}, {"kind": "play", "rank": 2}]

    async def test_registered_relationship_deserialization_restores_nested_properties(
        self, async_driver, driver_spec: DriverSpec, transform_client
    ):
        await create_transform_graph(async_driver, driver_spec)

        relationships = await transform_client.query(TransformKnows).execute()

        assert len(relationships) == 1
        assert isinstance(relationships[0], TransformKnows)
        assert relationships[0].metadata == {"since": 2024, "source": "manual"}
        assert relationships[0].history == [{"year": 2024, "level": "first"}]

    async def test_unregistered_node_raises_when_transformations_are_strict(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()
        async with async_driver.session() as session:
            await session.run("CREATE (:UnregisteredTransformNode {name: 'unregistered'})")

        with pytest.raises(
            SerializationError, match="No model with labels UnregisteredTransformNode registered"
        ):
            await client.query(UnregisteredTransformNode).execute()

    async def test_unregistered_relationship_raises_when_transformations_are_strict(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (:TransformPerson {name: 'Start', stored_name: 'Start'})
                CREATE (:TransformPerson {name: 'End', stored_name: 'End'})
                CREATE (:TransformPerson {name: 'Start'})-[:UNREGISTERED_TRANSFORM_RELATIONSHIP {
                    value: 'raw'
                }]->(:TransformPerson {name: 'End'})
                """
            )

        with pytest.raises(
            SerializationError,
            match="No model with type UNREGISTERED_TRANSFORM_RELATIONSHIP registered",
        ):
            await client.query(UnregisteredTransformRelationship).execute()

    async def test_unregistered_node_is_returned_as_native_entity_when_not_strict(
        self, async_driver, caplog
    ):
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()
        async with async_driver.session() as session:
            await session.run("CREATE (:UnregisteredTransformNode {name: 'raw'})")

        result = await client.query(UnregisteredTransformNode).execute()

        assert len(result) == 1
        assert isinstance(next(iter(cast(neo4j.graph.Node, result[0]).values())), neo4j.graph.Node)
        assert "No model with labels UnregisteredTransformNode registered" in caplog.text

    async def test_unregistered_relationship_is_returned_as_native_entity_when_not_strict(
        self, async_driver, caplog
    ):
        client = AsyncClient(async_driver, strict_transformations=False)
        await client.initialize()
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (:TransformPerson {name: 'Start', stored_name: 'Start'})
                CREATE (:TransformPerson {name: 'End', stored_name: 'End'})
                CREATE (:TransformPerson {name: 'Start'})-[:UNREGISTERED_TRANSFORM_RELATIONSHIP {
                    value: 'raw'
                }]->(:TransformPerson {name: 'End'})
                """
            )

        result = await client.query(UnregisteredTransformRelationship).execute()

        assert len(result) == 1
        assert isinstance(
            next(iter(cast(neo4j.graph.Node, result[0]).values())), neo4j.graph.Relationship
        )
        assert "No model with type UNREGISTERED_TRANSFORM_RELATIONSHIP registered" in caplog.text


class TestAsyncModelSerialization:
    async def test_nested_node_serialization_and_deserialization_with_client_option(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(TransformPerson)
        async with async_client_session(client) as session:
            session.change_tracker.add(
                TransformPerson(
                    name="Alice",
                    display_name="A. Example",
                    payload={"city": "Paris", "score": 7},
                    entries=[{"kind": "work", "rank": 1}],
                )
            )
            await session.change_tracker.flush()

        counts = await get_transform_graph_counts(async_driver)
        assert counts == (1, 0)
        people = await client.query(TransformPerson).execute()
        assert len(people) == 1
        assert people[0].payload == {"city": "Paris", "score": 7}
        assert people[0].entries == [{"kind": "work", "rank": 1}]
        assert people[0].display_name == "A. Example"

    async def test_nested_relationship_serialization_and_deserialization(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(TransformPerson, TransformKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = TransformKnows(
            metadata={"since": 2024}, history=[{"year": 2024, "level": "first"}]
        )

        async with async_client_session(client) as session:
            session.change_tracker.add(relationship, start, end)
            await session.change_tracker.flush()

        assert await get_transform_graph_counts(async_driver) == (2, 1)
        loaded = await client.query(TransformKnows).execute()
        assert loaded[0].metadata == {"since": 2024}
        assert loaded[0].history == [{"year": 2024, "level": "first"}]

    async def test_nested_node_serialization_rejects_disabled_client_option_on_neo4j(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=False)
        await client.initialize()
        client.register(TransformPerson)

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(SerializationError, match="Nested data types are only supported"):
                async with async_client_session(client) as session:
                    session.change_tracker.add(
                        TransformPerson(
                            name="Alice",
                            display_name="Alice",
                            payload={"city": "Paris"},
                        )
                    )
                    await session.change_tracker.flush()
            assert await get_transform_graph_counts(async_driver) == (0, 0)
        else:
            async with async_client_session(client) as session:
                session.change_tracker.add(
                    TransformPerson(
                        name="Alice",
                        display_name="Alice",
                        payload={"city": "Paris"},
                    )
                )
                await session.change_tracker.flush()
            loaded = await client.query(TransformPerson).execute()
            assert loaded[0].payload == {"city": "Paris"}

    async def test_nested_list_serialization_rejects_disabled_client_option_on_neo4j(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=False)
        await client.initialize()
        client.register(TransformPerson)
        node = TransformPerson(
            name="Alice", display_name="Alice", entries=[{"kind": "work", "rank": 1}]
        )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match=r"Nested data types are only supported.*TransformPerson.entries\[0\]",
            ):
                async with async_client_session(client) as session:
                    session.change_tracker.add(node)
                    await session.change_tracker.flush()
            assert await get_model_count(async_driver, "TransformPerson") == 0
        else:
            async with async_client_session(client) as session:
                session.change_tracker.add(node)
                await session.change_tracker.flush()
            loaded = await client.query(TransformPerson).execute()
            assert loaded[0].entries == [{"kind": "work", "rank": 1}]

    async def test_nested_relationship_serialization_respects_client_option(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=False)
        await client.initialize()
        client.register(TransformPerson, TransformKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = TransformKnows(
            metadata={"since": 2024}, history=[{"year": 2024, "level": "first"}]
        )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(SerializationError, match="Nested data types are only supported"):
                async with async_client_session(client) as session:
                    session.change_tracker.add(relationship, start, end)
                    await session.change_tracker.flush()
            assert await get_model_count(async_driver, "TransformPerson") == 0
            assert await get_transform_graph_counts(async_driver) == (0, 0)
        else:
            async with async_client_session(client) as session:
                session.change_tracker.add(relationship, start, end)
                await session.change_tracker.flush()
            loaded = await client.query(TransformKnows).execute()
            assert loaded[0].metadata == {"since": 2024}
            assert loaded[0].history == [{"year": 2024, "level": "first"}]

    async def test_model_serializer_and_deserializer_config_round_trip_node_and_relationship(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(CustomSerializedPerson, CustomSerializedKnows)
        start = CustomSerializedPerson(
            name="Alice", payload={"role": "start"}, events=[{"event": "created"}]
        )
        end = CustomSerializedPerson(
            name="Bob", payload={"role": "end"}, events=[{"event": "connected"}]
        )
        relationship = CustomSerializedKnows(metadata={"kind": "friend"}, events=[{"year": 2024}])

        async with async_client_session(client) as session:
            session.change_tracker.add(start)
            session.change_tracker.add(relationship, start, end)
            await session.change_tracker.flush()

        counts = await get_custom_graph_counts(async_driver)
        assert counts == (2, 1)
        people = await client.query(CustomSerializedPerson).execute()
        assert {person.payload["role"] for person in people} == {"start", "end"}
        assert {person.events[0]["event"] for person in people} == {"created", "connected"}
        relationships = await client.query(CustomSerializedKnows).execute()
        assert relationships[0].metadata == {"kind": "friend"}
        assert relationships[0].events == [{"year": 2024}]

    async def test_serializer_callback_is_used_only_for_neo4j_nested_values(
        self, async_driver, driver_spec: DriverSpec
    ):
        class FailingSerializerPerson(Node):
            name: str
            payload: dict[str, Any]

            loomi_config = {
                "labels": {"FailingSerializerPerson"},
                "serializer_fn": lambda _value: (_ for _ in ()).throw(ValueError("serialize")),
            }

        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(FailingSerializerPerson)

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(SerializationError, match="Field payload is not serializable"):
                async with async_client_session(client) as session:
                    session.change_tracker.add(
                        FailingSerializerPerson(name="Alice", payload={"data": 1})
                    )
                    await session.change_tracker.flush()
            assert await get_model_count(async_driver, "FailingSerializerPerson") == 0
        else:
            async with async_client_session(client) as session:
                session.change_tracker.add(
                    FailingSerializerPerson(name="Alice", payload={"data": 1})
                )
                await session.change_tracker.flush()
            assert await get_model_count(async_driver, "FailingSerializerPerson") == 1

    async def test_model_without_serializer_config_raises_serialization_error(self, async_driver):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(MissingSerializerPerson)

        with pytest.raises(SerializationError, match="No `serializer_fn` available"):
            async with async_client_session(client) as session:
                session.change_tracker.add(
                    MissingSerializerPerson(name="Alice", payload={"data": 1})
                )
                await session.change_tracker.flush()

        assert await get_model_count(async_driver, "MissingSerializerPerson") == 0

    async def test_model_without_deserializer_config_raises_during_database_transformation(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(MissingDeserializerPerson)
        async with async_driver.session() as session:
            await session.run("CREATE (:MissingDeserializerPerson {name: 'Alice'})")

        with pytest.raises(SerializationError, match="No `deserializer_fn` available"):
            await client.query(MissingDeserializerPerson).execute()

    async def test_deserializer_callback_is_used_only_for_neo4j_nested_values(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(FailingDeserializerPerson)
        async with async_driver.session() as session:
            if driver_spec.name.value == "Neo4j":
                await session.run(
                    "CREATE (:FailingDeserializerPerson {name: 'Alice', payload: 'wrapped'})"
                )
            else:
                await session.run(
                    "CREATE (:FailingDeserializerPerson {name: 'Alice', payload: $payload})",
                    payload={"data": 1},
                )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match="Serialized value at payload could not be deserialized",
            ):
                await client.query(FailingDeserializerPerson).execute()
        else:
            result = await client.query(FailingDeserializerPerson).execute()
            assert result[0].payload == {"data": 1}

    async def test_list_item_deserializer_failure_is_wrapped_for_neo4j(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(FailingDeserializerListPerson)
        async with async_driver.session() as session:
            if driver_spec.name.value == "Neo4j":
                await session.run(
                    "CREATE (:FailingDeserializerListPerson "
                    "{name: 'Alice', events: ['unparseable']})"
                )
            else:
                await session.run(
                    "CREATE (:FailingDeserializerListPerson {name: 'Alice', events: $events})",
                    events=[{"event": "native"}],
                )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match="Serialized value at events could not be deserialized",
            ):
                await client.query(FailingDeserializerListPerson).execute()
        else:
            result = await client.query(FailingDeserializerListPerson).execute()
            assert result[0].events == [{"event": "native"}]

    async def test_deserialization_skips_unknown_database_properties(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(TransformPerson)
        async with async_driver.session() as session:
            await session.run(
                """
                CREATE (:TransformPerson {
                    name: 'Alice', stored_name: 'A. Example',
                    unexpected_property: 'ignored'
                })
                """
            )

        people = await client.query(TransformPerson).execute()

        assert len(people) == 1
        assert people[0].display_name == "A. Example"
        assert not hasattr(people[0], "unexpected_property")


@asynccontextmanager
async def async_client_session(client: AsyncClient) -> AsyncIterator[Any]:
    async with client.session() as session:
        yield session


async def get_custom_graph_counts(async_driver) -> tuple[int, int]:
    async with async_driver.session() as session:
        nodes = await session.run(
            "MATCH (person:CustomSerializedPerson) RETURN count(person) AS count"
        )
        node_record = await nodes.single()
        relationships = await session.run(
            "MATCH ()-[relationship:CUSTOM_SERIALIZED_KNOWS]->() "
            "RETURN count(relationship) AS count"
        )
        relationship_record = await relationships.single()

    assert node_record is not None
    assert relationship_record is not None
    return node_record["count"], relationship_record["count"]


async def get_model_count(async_driver, label: str) -> int:
    async with async_driver.session() as session:
        result = await session.run(f"MATCH (entity:{label}) RETURN count(entity) AS count")  # type: ignore
        record = await result.single()
    assert record is not None
    return record["count"]


async def get_relationship_count(async_driver, relationship_type: str) -> int:
    async with async_driver.session() as session:
        result = await session.run(
            f"MATCH ()-[relationship:{relationship_type}]->() RETURN count(relationship) AS count"
        )
        record = await result.single()
    assert record is not None
    return record["count"]


class TestAsyncUnsupportedModelValues:
    async def test_unsupported_node_field_type_raises_and_does_not_persist(self, async_driver):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(UnsupportedValuePerson)

        with pytest.raises(
            SerializationError, match=r"Data type <class 'tuple'> can not be stored"
        ):
            async with async_client_session(client) as session:
                session.change_tracker.add(
                    UnsupportedValuePerson(name="Alice", payload=("not", "a", "property"))
                )
                await session.change_tracker.flush()

        assert await get_model_count(async_driver, "UnsupportedValuePerson") == 0

    async def test_unsupported_relationship_field_type_raises_and_rolls_back_endpoints(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        await client.initialize()
        client.register(TransformPerson, UnsupportedValueKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = UnsupportedValueKnows(payload=("not", "a", "property"))

        with pytest.raises(
            SerializationError, match=r"Data type <class 'tuple'> can not be stored"
        ):
            async with async_client_session(client) as session:
                session.change_tracker.add(relationship, start, end)
                await session.change_tracker.flush()

        assert await get_model_count(async_driver, "TransformPerson") == 0
        assert await get_relationship_count(async_driver, "UNSUPPORTED_VALUE_KNOWS") == 0


class TestAsyncNestedListSerializerFailures:
    async def test_node_list_item_serializer_failure_is_wrapped_on_neo4j(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(FailingListSerializerPerson)

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match=r"Field events\[0\] is not serializable",
            ):
                async with async_client_session(client) as session:
                    session.change_tracker.add(
                        FailingListSerializerPerson(name="Alice", events=[{"kind": "event"}])
                    )
                    await session.change_tracker.flush()
            assert await get_model_count(async_driver, "FailingListSerializerPerson") == 0
        else:
            async with async_client_session(client) as session:
                session.change_tracker.add(
                    FailingListSerializerPerson(name="Alice", events=[{"kind": "event"}])
                )
                await session.change_tracker.flush()
            loaded = await client.query(FailingListSerializerPerson).execute()
            assert loaded[0].events == [{"kind": "event"}]

    async def test_relationship_list_item_serializer_failure_is_wrapped_on_neo4j(
        self, async_driver, driver_spec: DriverSpec
    ):
        client = AsyncClient(async_driver, serialize_nested=True)
        await client.initialize()
        client.register(TransformPerson, FailingListSerializerKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = FailingListSerializerKnows(events=[{"kind": "event"}])

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match=r"Field events\[0\] is not serializable",
            ):
                async with async_client_session(client) as session:
                    session.change_tracker.add(relationship, start, end)
                    await session.change_tracker.flush()
            assert await get_model_count(async_driver, "TransformPerson") == 0
            assert await get_relationship_count(async_driver, "FAILING_LIST_SERIALIZER_KNOWS") == 0
        else:
            async with async_client_session(client) as session:
                session.change_tracker.add(relationship, start, end)
                await session.change_tracker.flush()
            loaded = await client.query(FailingListSerializerKnows).execute()
            assert loaded[0].events == [{"kind": "event"}]
