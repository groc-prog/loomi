# pylint: disable=missing-class-docstring, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long

import json
from contextlib import contextmanager
from typing import Any, Iterator, cast

import neo4j
import neo4j.graph
import pytest
from pydantic import Field

from loomi._sync.client import Client
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
def transform_client(sync_driver: neo4j.Driver):
    client = Client(sync_driver, serialize_nested=True)
    client.initialize()
    client.register(TransformPerson, TransformKnows)
    return client


def create_transform_graph(sync_driver: neo4j.Driver, driver_spec: DriverSpec) -> None:
    with sync_driver.session() as session:
        if driver_spec.name.value == "Neo4j":
            session.run(
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
            session.run(
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


def get_transform_graph_counts(sync_driver: neo4j.Driver) -> tuple[int, int]:
    with sync_driver.session() as session:
        nodes = session.run("MATCH (person:TransformPerson) RETURN count(person) AS count")
        node_record = nodes.single()
        relationships = session.run(
            "MATCH ()-[relationship:TRANSFORM_KNOWS]->() RETURN count(relationship) AS count"
        )
        relationship_record = relationships.single()

    assert node_record is not None
    assert relationship_record is not None
    return node_record["count"], relationship_record["count"]


class TestSyncModelTransformation:
    def test_registered_node_deserialization_maps_alias_and_skips_unknown_fields(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec, transform_client
    ):
        create_transform_graph(sync_driver, driver_spec)

        people = transform_client.query(TransformPerson).execute()

        assert {person.name for person in people} == {"Alice", "Bob"}
        alice = next(person for person in people if person.name == "Alice")
        assert alice.display_name == "A. Example"
        assert alice.tags == ["alice"]
        assert alice.payload == {"city": "Paris", "score": 7}
        assert alice.entries == [{"kind": "work", "rank": 1}, {"kind": "play", "rank": 2}]

    def test_registered_relationship_deserialization_restores_nested_properties(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec, transform_client
    ):
        create_transform_graph(sync_driver, driver_spec)

        relationships = transform_client.query(TransformKnows).execute()

        assert len(relationships) == 1
        assert isinstance(relationships[0], TransformKnows)
        assert relationships[0].metadata == {"since": 2024, "source": "manual"}
        assert relationships[0].history == [{"year": 2024, "level": "first"}]

    def test_unregistered_node_raises_when_transformations_are_strict(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        with sync_driver.session() as session:
            session.run("CREATE (:UnregisteredTransformNode {name: 'unregistered'})")

        with pytest.raises(
            SerializationError, match="No model with labels UnregisteredTransformNode registered"
        ):
            client.query(UnregisteredTransformNode).execute()

    def test_unregistered_relationship_raises_when_transformations_are_strict(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        with sync_driver.session() as session:
            session.run(
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
            client.query(UnregisteredTransformRelationship).execute()

    def test_unregistered_node_is_returned_as_native_entity_when_not_strict(
        self, sync_driver: neo4j.Driver, caplog
    ):
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()
        with sync_driver.session() as session:
            session.run("CREATE (:UnregisteredTransformNode {name: 'raw'})")

        result = client.query(UnregisteredTransformNode).execute()

        assert len(result) == 1
        assert isinstance(next(iter(cast(neo4j.graph.Node, result[0]).values())), neo4j.graph.Node)
        assert "No model with labels UnregisteredTransformNode registered" in caplog.text

    def test_unregistered_relationship_is_returned_as_native_entity_when_not_strict(
        self, sync_driver: neo4j.Driver, caplog
    ):
        client = Client(sync_driver, strict_transformations=False)
        client.initialize()
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (:TransformPerson {name: 'Start', stored_name: 'Start'})
                CREATE (:TransformPerson {name: 'End', stored_name: 'End'})
                CREATE (:TransformPerson {name: 'Start'})-[:UNREGISTERED_TRANSFORM_RELATIONSHIP {
                    value: 'raw'
                }]->(:TransformPerson {name: 'End'})
                """
            )

        result = client.query(UnregisteredTransformRelationship).execute()

        assert len(result) == 1
        assert isinstance(
            next(iter(cast(neo4j.graph.Node, result[0]).values())), neo4j.graph.Relationship
        )
        assert "No model with type UNREGISTERED_TRANSFORM_RELATIONSHIP registered" in caplog.text


class TestSyncModelSerialization:
    def test_nested_node_serialization_and_deserialization_with_client_option(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(TransformPerson)
        with sync_client_session(client) as session:
            session.change_tracker.add(
                TransformPerson(
                    name="Alice",
                    display_name="A. Example",
                    payload={"city": "Paris", "score": 7},
                    entries=[{"kind": "work", "rank": 1}],
                )
            )
            session.change_tracker.flush()

        counts = get_transform_graph_counts(sync_driver)
        assert counts == (1, 0)
        people = client.query(TransformPerson).execute()
        assert len(people) == 1
        assert people[0].payload == {"city": "Paris", "score": 7}
        assert people[0].entries == [{"kind": "work", "rank": 1}]
        assert people[0].display_name == "A. Example"

    def test_nested_relationship_serialization_and_deserialization(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(TransformPerson, TransformKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = TransformKnows(
            metadata={"since": 2024}, history=[{"year": 2024, "level": "first"}]
        )

        with sync_client_session(client) as session:
            session.change_tracker.add(relationship, start, end)
            session.change_tracker.flush()

        assert get_transform_graph_counts(sync_driver) == (2, 1)
        loaded = client.query(TransformKnows).execute()
        assert loaded[0].metadata == {"since": 2024}
        assert loaded[0].history == [{"year": 2024, "level": "first"}]

    def test_nested_node_serialization_rejects_disabled_client_option_on_neo4j(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=False)
        client.initialize()
        client.register(TransformPerson)

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(SerializationError, match="Nested data types are only supported"):
                with sync_client_session(client) as session:
                    session.change_tracker.add(
                        TransformPerson(
                            name="Alice",
                            display_name="Alice",
                            payload={"city": "Paris"},
                        )
                    )
                    session.change_tracker.flush()
            assert get_transform_graph_counts(sync_driver) == (0, 0)
        else:
            with sync_client_session(client) as session:
                session.change_tracker.add(
                    TransformPerson(
                        name="Alice",
                        display_name="Alice",
                        payload={"city": "Paris"},
                    )
                )
                session.change_tracker.flush()
            loaded = client.query(TransformPerson).execute()
            assert loaded[0].payload == {"city": "Paris"}

    def test_nested_list_serialization_rejects_disabled_client_option_on_neo4j(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=False)
        client.initialize()
        client.register(TransformPerson)
        node = TransformPerson(
            name="Alice", display_name="Alice", entries=[{"kind": "work", "rank": 1}]
        )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match=r"Nested data types are only supported.*TransformPerson.entries\[0\]",
            ):
                with sync_client_session(client) as session:
                    session.change_tracker.add(node)
                    session.change_tracker.flush()
            assert get_model_count(sync_driver, "TransformPerson") == 0
        else:
            with sync_client_session(client) as session:
                session.change_tracker.add(node)
                session.change_tracker.flush()
            loaded = client.query(TransformPerson).execute()
            assert loaded[0].entries == [{"kind": "work", "rank": 1}]

    def test_nested_relationship_serialization_respects_client_option(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=False)
        client.initialize()
        client.register(TransformPerson, TransformKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = TransformKnows(
            metadata={"since": 2024}, history=[{"year": 2024, "level": "first"}]
        )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(SerializationError, match="Nested data types are only supported"):
                with sync_client_session(client) as session:
                    session.change_tracker.add(relationship, start, end)
                    session.change_tracker.flush()
            assert get_model_count(sync_driver, "TransformPerson") == 0
            assert get_transform_graph_counts(sync_driver) == (0, 0)
        else:
            with sync_client_session(client) as session:
                session.change_tracker.add(relationship, start, end)
                session.change_tracker.flush()
            loaded = client.query(TransformKnows).execute()
            assert loaded[0].metadata == {"since": 2024}
            assert loaded[0].history == [{"year": 2024, "level": "first"}]

    def test_model_serializer_and_deserializer_config_round_trip_node_and_relationship(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(CustomSerializedPerson, CustomSerializedKnows)
        start = CustomSerializedPerson(
            name="Alice", payload={"role": "start"}, events=[{"event": "created"}]
        )
        end = CustomSerializedPerson(
            name="Bob", payload={"role": "end"}, events=[{"event": "connected"}]
        )
        relationship = CustomSerializedKnows(metadata={"kind": "friend"}, events=[{"year": 2024}])

        with sync_client_session(client) as session:
            session.change_tracker.add(start)
            session.change_tracker.add(relationship, start, end)
            session.change_tracker.flush()

        counts = get_custom_graph_counts(sync_driver)
        assert counts == (2, 1)
        people = client.query(CustomSerializedPerson).execute()
        assert {person.payload["role"] for person in people} == {"start", "end"}
        assert {person.events[0]["event"] for person in people} == {"created", "connected"}
        relationships = client.query(CustomSerializedKnows).execute()
        assert relationships[0].metadata == {"kind": "friend"}
        assert relationships[0].events == [{"year": 2024}]

    def test_serializer_callback_is_used_only_for_neo4j_nested_values(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        class FailingSerializerPerson(Node):
            name: str
            payload: dict[str, Any]

            loomi_config = {
                "labels": {"FailingSerializerPerson"},
                "serializer_fn": lambda _value: (_ for _ in ()).throw(ValueError("serialize")),
            }

        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(FailingSerializerPerson)

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(SerializationError, match="Field payload is not serializable"):
                with sync_client_session(client) as session:
                    session.change_tracker.add(
                        FailingSerializerPerson(name="Alice", payload={"data": 1})
                    )
                    session.change_tracker.flush()
            assert get_model_count(sync_driver, "FailingSerializerPerson") == 0
        else:
            with sync_client_session(client) as session:
                session.change_tracker.add(
                    FailingSerializerPerson(name="Alice", payload={"data": 1})
                )
                session.change_tracker.flush()
            assert get_model_count(sync_driver, "FailingSerializerPerson") == 1

    def test_model_without_serializer_config_raises_serialization_error(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(MissingSerializerPerson)

        with pytest.raises(SerializationError, match="No `serializer_fn` available"):
            with sync_client_session(client) as session:
                session.change_tracker.add(
                    MissingSerializerPerson(name="Alice", payload={"data": 1})
                )
                session.change_tracker.flush()

        assert get_model_count(sync_driver, "MissingSerializerPerson") == 0

    def test_model_without_deserializer_config_raises_during_database_transformation(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        client.register(MissingDeserializerPerson)
        with sync_driver.session() as session:
            session.run("CREATE (:MissingDeserializerPerson {name: 'Alice'})")

        with pytest.raises(SerializationError, match="No `deserializer_fn` available"):
            client.query(MissingDeserializerPerson).execute()

    def test_deserializer_callback_is_used_only_for_neo4j_nested_values(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(FailingDeserializerPerson)
        with sync_driver.session() as session:
            if driver_spec.name.value == "Neo4j":
                session.run(
                    "CREATE (:FailingDeserializerPerson {name: 'Alice', payload: 'wrapped'})"
                )
            else:
                session.run(
                    "CREATE (:FailingDeserializerPerson {name: 'Alice', payload: $payload})",
                    payload={"data": 1},
                )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match="Serialized value at payload could not be deserialized",
            ):
                client.query(FailingDeserializerPerson).execute()
        else:
            result = client.query(FailingDeserializerPerson).execute()
            assert result[0].payload == {"data": 1}

    def test_list_item_deserializer_failure_is_wrapped_for_neo4j(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(FailingDeserializerListPerson)
        with sync_driver.session() as session:
            if driver_spec.name.value == "Neo4j":
                session.run(
                    "CREATE (:FailingDeserializerListPerson "
                    "{name: 'Alice', events: ['unparseable']})"
                )
            else:
                session.run(
                    "CREATE (:FailingDeserializerListPerson {name: 'Alice', events: $events})",
                    events=[{"event": "native"}],
                )

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match="Serialized value at events could not be deserialized",
            ):
                client.query(FailingDeserializerListPerson).execute()
        else:
            result = client.query(FailingDeserializerListPerson).execute()
            assert result[0].events == [{"event": "native"}]

    def test_deserialization_skips_unknown_database_properties(self, sync_driver: neo4j.Driver):
        client = Client(sync_driver)
        client.initialize()
        client.register(TransformPerson)
        with sync_driver.session() as session:
            session.run(
                """
                CREATE (:TransformPerson {
                    name: 'Alice', stored_name: 'A. Example',
                    unexpected_property: 'ignored'
                })
                """
            )

        people = client.query(TransformPerson).execute()

        assert len(people) == 1
        assert people[0].display_name == "A. Example"
        assert not hasattr(people[0], "unexpected_property")


@contextmanager
def sync_client_session(client: Client) -> Iterator[Any]:
    with client.session() as session:
        yield session


def get_custom_graph_counts(sync_driver: neo4j.Driver) -> tuple[int, int]:
    with sync_driver.session() as session:
        nodes = session.run("MATCH (person:CustomSerializedPerson) RETURN count(person) AS count")
        node_record = nodes.single()
        relationships = session.run(
            "MATCH ()-[relationship:CUSTOM_SERIALIZED_KNOWS]->() "
            "RETURN count(relationship) AS count"
        )
        relationship_record = relationships.single()

    assert node_record is not None
    assert relationship_record is not None
    return node_record["count"], relationship_record["count"]


def get_model_count(sync_driver: neo4j.Driver, label: str) -> int:
    with sync_driver.session() as session:
        result = session.run(f"MATCH (entity:{label}) RETURN count(entity) AS count")  # type: ignore
        record = result.single()
    assert record is not None
    return record["count"]


def get_relationship_count(sync_driver: neo4j.Driver, relationship_type: str) -> int:
    with sync_driver.session() as session:
        result = session.run(
            f"MATCH ()-[relationship:{relationship_type}]->() RETURN count(relationship) AS count"
        )
        record = result.single()
    assert record is not None
    return record["count"]


class TestSyncUnsupportedModelValues:
    def test_unsupported_node_field_type_raises_and_does_not_persist(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        client.register(UnsupportedValuePerson)

        with pytest.raises(
            SerializationError, match=r"Data type <class 'tuple'> can not be stored"
        ):
            with sync_client_session(client) as session:
                session.change_tracker.add(
                    UnsupportedValuePerson(name="Alice", payload=("not", "a", "property"))
                )
                session.change_tracker.flush()

        assert get_model_count(sync_driver, "UnsupportedValuePerson") == 0

    def test_unsupported_relationship_field_type_raises_and_rolls_back_endpoints(
        self, sync_driver: neo4j.Driver
    ):
        client = Client(sync_driver)
        client.initialize()
        client.register(TransformPerson, UnsupportedValueKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = UnsupportedValueKnows(payload=("not", "a", "property"))

        with pytest.raises(
            SerializationError, match=r"Data type <class 'tuple'> can not be stored"
        ):
            with sync_client_session(client) as session:
                session.change_tracker.add(relationship, start, end)
                session.change_tracker.flush()

        assert get_model_count(sync_driver, "TransformPerson") == 0
        assert get_relationship_count(sync_driver, "UNSUPPORTED_VALUE_KNOWS") == 0


class TestSyncNestedListSerializerFailures:
    def test_node_list_item_serializer_failure_is_wrapped_on_neo4j(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(FailingListSerializerPerson)

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match=r"Field events\[0\] is not serializable",
            ):
                with sync_client_session(client) as session:
                    session.change_tracker.add(
                        FailingListSerializerPerson(name="Alice", events=[{"kind": "event"}])
                    )
                    session.change_tracker.flush()
            assert get_model_count(sync_driver, "FailingListSerializerPerson") == 0
        else:
            with sync_client_session(client) as session:
                session.change_tracker.add(
                    FailingListSerializerPerson(name="Alice", events=[{"kind": "event"}])
                )
                session.change_tracker.flush()
            loaded = client.query(FailingListSerializerPerson).execute()
            assert loaded[0].events == [{"kind": "event"}]

    def test_relationship_list_item_serializer_failure_is_wrapped_on_neo4j(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        client = Client(sync_driver, serialize_nested=True)
        client.initialize()
        client.register(TransformPerson, FailingListSerializerKnows)
        start = TransformPerson(name="Alice", display_name="Alice")
        end = TransformPerson(name="Bob", display_name="Bob")
        relationship = FailingListSerializerKnows(events=[{"kind": "event"}])

        if driver_spec.name.value == "Neo4j":
            with pytest.raises(
                SerializationError,
                match=r"Field events\[0\] is not serializable",
            ):
                with sync_client_session(client) as session:
                    session.change_tracker.add(relationship, start, end)
                    session.change_tracker.flush()
            assert get_model_count(sync_driver, "TransformPerson") == 0
            assert get_relationship_count(sync_driver, "FAILING_LIST_SERIALIZER_KNOWS") == 0
        else:
            with sync_client_session(client) as session:
                session.change_tracker.add(relationship, start, end)
                session.change_tracker.flush()
            loaded = client.query(FailingListSerializerKnows).execute()
            assert loaded[0].events == [{"kind": "event"}]
