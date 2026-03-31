# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import LiteralString, cast

import neo4j
import pytest
from pydantic import BaseModel

from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.expressions import QueryCompilationContext, QueryExpression
from loomi.query.functions.comparison import equals
from loomi.query.functions.transformation import to_lower
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class Human(Node):
    name: str
    age: int


aliased_human = create_alias(Human, "human")


class TestToLowerDbFunction:
    @pytest.mark.integration
    def test_to_lower_db_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated toLower queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(to_lower(Human.name), "john")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_lower_db_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated toLower queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "john"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "jane"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, to_lower("John"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "john"

    @pytest.mark.integration
    def test_to_lower_db_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated toLower queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(to_lower(Human.name), to_lower("John"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"
