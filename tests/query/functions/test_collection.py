# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import List, LiteralString, cast

import neo4j
import pytest
from pydantic import BaseModel

from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.expressions import CompilationContext, Expression
from loomi.query.functions.collection import all_, any_, none, single
from loomi.query.functions.comparison import equals
from tests.fixtures.db import (
    MEMGRAPH_DRIVER_SPEC,
    DriverSpec,
    driver_spec,
    sync_cleanup,
    sync_driver,
)


class Human(Node):
    name: str
    jobs: List[str]


aliased_human = create_alias(Human, "human")


class TestAnyListExpressions:
    @pytest.mark.integration
    def test_any_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ANY queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(any_(Human.jobs), "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_any_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ANY queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(any_(aliased_human.jobs), "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestAllListExpressions:
    @pytest.mark.integration
    def test_all_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ALL queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(all_(Human.jobs), "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_all_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ALL queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(all_(aliased_human.jobs), "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestNoneListExpressions:
    @pytest.mark.integration
    def test_none_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated NONE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(none(Human.jobs), "Artist")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_none_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated NONE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(none(aliased_human.jobs), "Artist")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestSingleListExpressions:
    @pytest.mark.integration
    def test_single_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated SINGLE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Developer", "Developer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(single(Human.jobs), "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_single_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated SINGLE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Developer", "Developer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(single(aliased_human.jobs), "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestIndexListExpressions:
    @pytest.mark.integration
    def test_index_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated SINGLE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.jobs[0], "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_index_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated SINGLE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "jobs": ["Developer", "Engineer"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "jobs": ["Artist", "Designer"]}},
            )

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(aliased_human.jobs[0], "Developer")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestMemgraphSpecificExpression:
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

            ctx = CompilationContext(MEMGRAPH_DRIVER_SPEC.name)
            ctx.add_model(Worker)
            expression = equals(single(any_(Worker.jobs).tags), "tag3")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Worker)}:Worker) WHERE {compiled_expression} RETURN {ctx.get_variable(Worker)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"
