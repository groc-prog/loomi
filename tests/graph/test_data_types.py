# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import datetime
from typing import Annotated

import neo4j
import neo4j.time
import pytest
from pydantic import BeforeValidator

from loomi._sync.client import Client
from loomi.constants import ServerType
from loomi.graph.data_types import (
    Neo4jTemporalDate,
    Neo4jTemporalDateAnnotation,
    Neo4jTemporalDateTime,
    Neo4jTemporalDateTimeAnnotation,
    Neo4jTemporalTime,
    Neo4jTemporalTimeAnnotation,
)
from loomi.graph.node import Node
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class TestNeo4jDate:
    @pytest.mark.integration
    def test_neo4j_date_data_type(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the client can handle Neo4j dates."""

        class Human(Node):
            birthday: Neo4jTemporalDate

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        birthday = neo4j.time.Date(2026, 4, 12)
        with client.session() as session:
            human = Human(birthday=birthday)

            session.change_tracker.add(human)
            session.change_tracker.flush()

            result = session.run("MATCH (n:Human) RETURN n")
            data = result.value()

            assert isinstance(data[0], Human)
            assert isinstance(data[0].birthday, neo4j.time.Date)
            assert data[0].birthday == birthday

    @pytest.mark.integration
    def test_native_date_data_type(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the client can handle native dates when coerced."""

        class Human(Node):
            birthday: Annotated[datetime.date, BeforeValidator(Neo4jTemporalDateAnnotation.coerce)]

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        birthday = neo4j.time.Date(2026, 4, 12)
        with client.session() as session:
            human = Human(birthday=birthday)
            session.change_tracker.add(human)
            session.change_tracker.flush()

            result = session.run("MATCH (n:Human) RETURN n")
            data = result.value()

            assert isinstance(data[0], Human)
            assert isinstance(data[0].birthday, datetime.date)
            assert data[0].birthday == birthday

    def test_neo4j_date_json_schema(self):
        """Verify that the model JSON schema for Neo4j dates is correct."""

        class Human(Node):
            birthday: Neo4jTemporalDate

        schema = Human.model_json_schema()

        assert "properties" in schema
        assert "birthday" in schema["properties"]
        assert "type" in schema["properties"]["birthday"]
        assert "format" in schema["properties"]["birthday"]
        assert schema["properties"]["birthday"]["type"] == "string"
        assert schema["properties"]["birthday"]["format"] == "date"


class TestNeo4jTime:
    @pytest.mark.integration
    def test_neo4j_time_data_type(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the client can handle Neo4j time."""

        class Human(Node):
            works_until: Neo4jTemporalTime

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        works_until = neo4j.time.Time(12, 24, 56, 12)
        with client.session() as session:
            human = Human(works_until=works_until)
            session.change_tracker.add(human)
            session.change_tracker.flush()

            result = session.run("MATCH (n:Human) RETURN n")
            data = result.value()

            assert isinstance(data[0], Human)
            assert isinstance(data[0].works_until, neo4j.time.Time)

            if driver_spec.name == ServerType.NEO4J:
                assert data[0].works_until == works_until
            else:
                assert data[0].works_until == neo4j.time.Time(12, 24, 56, 0)

    @pytest.mark.integration
    def test_native_time_data_type(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the client can handle native time when coerced."""

        class Human(Node):
            works_until: Annotated[
                datetime.time, BeforeValidator(Neo4jTemporalTimeAnnotation.coerce)
            ]

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        works_until = neo4j.time.Time(12, 24, 56, 12)
        with client.session() as session:
            human = Human(works_until=works_until)
            session.change_tracker.add(human)
            session.change_tracker.flush()

            result = session.run("MATCH (n:Human) RETURN n")
            data = result.value()

            assert isinstance(data[0], Human)
            assert isinstance(data[0].works_until, datetime.time)
            assert data[0].works_until == neo4j.time.Time(12, 24, 56, 0)

    def test_neo4j_time_json_schema(self):
        """Verify that the model JSON schema for Neo4j time is correct."""

        class Human(Node):
            works_until: Neo4jTemporalTime

        schema = Human.model_json_schema()

        assert "properties" in schema
        assert "works_until" in schema["properties"]
        assert "type" in schema["properties"]["works_until"]
        assert "format" in schema["properties"]["works_until"]
        assert schema["properties"]["works_until"]["type"] == "string"
        assert schema["properties"]["works_until"]["format"] == "time"


class TestNeo4jDateTime:
    @pytest.mark.integration
    def test_neo4j_datetime_data_type(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the client can handle Neo4j datetime."""

        class Human(Node):
            retires_at: Neo4jTemporalDateTime

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        retires_at = neo4j.time.DateTime(2026, 4, 26, 12, 6, 23, 12)
        with client.session() as session:
            human = Human(retires_at=retires_at)
            session.change_tracker.add(human)
            session.change_tracker.flush()

            result = session.run("MATCH (n:Human) RETURN n")
            data = result.value()

            assert isinstance(data[0], Human)
            assert isinstance(data[0].retires_at, neo4j.time.DateTime)

            if driver_spec.name == ServerType.NEO4J:
                assert data[0].retires_at == retires_at
            else:
                assert data[0].retires_at == neo4j.time.DateTime(2026, 4, 26, 12, 6, 23, 0)

    @pytest.mark.integration
    def test_native_datetime_data_type(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the client can handle native datetime when coerced."""

        class Human(Node):
            retires_at: Annotated[
                datetime.datetime, BeforeValidator(Neo4jTemporalDateTimeAnnotation.coerce)
            ]

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        retires_at = neo4j.time.DateTime(2026, 4, 26, 12, 6, 23, 12)
        with client.session() as session:
            human = Human(retires_at=retires_at)
            session.change_tracker.add(human)
            session.change_tracker.flush()

            result = session.run("MATCH (n:Human) RETURN n")
            data = result.value()

            assert isinstance(data[0], Human)
            assert isinstance(data[0].retires_at, datetime.datetime)
            assert data[0].retires_at == neo4j.time.DateTime(2026, 4, 26, 12, 6, 23, 0)

    def test_neo4j_datetime_json_schema(self):
        """Verify that the model JSON schema for Neo4j datetime is correct."""

        class Human(Node):
            retires_at: Neo4jTemporalDateTime

        schema = Human.model_json_schema()

        assert "properties" in schema
        assert "retires_at" in schema["properties"]
        assert "type" in schema["properties"]["retires_at"]
        assert "format" in schema["properties"]["retires_at"]
        assert schema["properties"]["retires_at"]["type"] == "string"
        assert schema["properties"]["retires_at"]["format"] == "date-time"
