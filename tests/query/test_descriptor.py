# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import List, LiteralString, cast

import neo4j
import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.query.expressions import ExpressionContext
from loomi.query.functions import all_, any_, element_id, equals, id_, in_, none, single
from tests.fixtures.db import (
    MEMGRAPH_DRIVER_SPEC,
    DriverSpec,
    driver_spec,
    sync_cleanup,
    sync_driver,
)


class Tag(BaseModel):
    name: str


class Metadata(BaseModel):
    id_: str
    tags: List[Tag]


class Job(BaseModel):
    name: str


class Human(Node):
    name: str
    meta: Metadata
    job: Job
    hobbies: List[str]


class TestPropertyDescriptorListPaths:
    @pytest.mark.integration
    def test_any_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ANY property path can be used by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Coding", "Chilling"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Sleeping", "Working"]}},
            )

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(any_(Human.hobbies), "Coding")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_all_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ALL property path can be used by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Coding", "Chilling"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Sleeping", "Working"]}},
            )

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = in_(all_(Human.hobbies), ["Coding", "Chilling"])
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_none_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated NONE property path can be used by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Coding", "Chilling"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Sleeping", "Working"]}},
            )

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(none(Human.hobbies), "Working")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_single_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated SINGLE property path can be used by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Coding", "Chilling"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Sleeping", "Working"]}},
            )

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = in_(single(Human.hobbies), ["Sleeping", "Working", "Chilling"])
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_index_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated property path with a index can be used by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Coding", "Chilling"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Sleeping", "Working"]}},
            )

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.hobbies[0], "Coding")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_path_query(self):
        """Verify that the generated nested property path can be used by the Memgraph driver."""
        driver = neo4j.GraphDatabase.driver(
            cast(str, MEMGRAPH_DRIVER_SPEC.uri),
            auth=(cast(str, MEMGRAPH_DRIVER_SPEC.user), cast(str, MEMGRAPH_DRIVER_SPEC.pwd)),
        )
        sync_cleanup(driver, MEMGRAPH_DRIVER_SPEC.name)

        class Job(BaseModel):
            tags: List[str]

        class Worker(Node):
            name: str
            jobs: List[Job]

        with driver.session() as session:
            session.run(
                "CREATE (:Worker $props)",
                {
                    "props": {
                        "name": "John",
                        "jobs": [{"tags": ["tag1", "tag2"]}, {"tags": ["tag3", "tag4"]}],
                    }
                },
            )
            session.run(
                "CREATE (:Worker $props)",
                {
                    "props": {
                        "name": "Jane",
                        "jobs": [{"tags": ["tag8", "tag7"]}, {"tags": ["tag6", "tag5"]}],
                    }
                },
            )

            ctx = ExpressionContext(MEMGRAPH_DRIVER_SPEC.name)
            ctx.add_model(Worker)
            expression = equals(single(any_(Worker.jobs).tags), "tag3")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Worker)}:Worker) WHERE {compiled_expression} RETURN {ctx.get_variable(Worker)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestEntityIdDescriptor:
    @pytest.mark.integration
    def test_element_id_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated property path with a element id can be used by the driver."""
        with sync_driver.session() as session:
            seed_query = f"CREATE (n:Human $props) RETURN {'elementId(n)' if driver_spec.name == ServerType.NEO4J else 'id(n)'}"
            seed_result = session.run(
                cast(LiteralString, seed_query),
                {"props": {"name": "John"}},
            )
            entity_id = seed_result.value()[0]

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(element_id(Human, driver_spec.name), entity_id)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_id_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated property path with a element id can be used by the driver."""
        with sync_driver.session() as session:
            seed_result = session.run(
                "CREATE (n:Human $props) RETURN id(n)",
                {"props": {"name": "John"}},
            )
            entity_id = seed_result.value()[0]

            ctx = ExpressionContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(id_(Human, driver_spec.name), entity_id)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"
