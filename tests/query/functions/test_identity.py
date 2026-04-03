# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import LiteralString, cast

import neo4j
import pytest

from loomi.constants import ServerType
from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.expressions import ComparisonExpression, CompilationContext
from loomi.query.functions.comparison import equals
from loomi.query.functions.identity import element_id, id_
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class Human(Node):
    name: str


aliased_human = create_alias(Human, "human")


class TestElementIdExpressions:
    @pytest.mark.integration
    def test_element_id_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated elementId queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            operator = "elementId" if driver_spec.name != ServerType.MEMGRAPH else "id"
            result = session.run(
                f"CREATE (h:Human $props) RETURN {operator}(h)",
                {"props": {"name": "John"}},
            )
            identifier = result.value()[0]

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(element_id(Human), identifier)
            compiled_expression = cast(ComparisonExpression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_element_id_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated elementId queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            operator = "elementId" if driver_spec.name != ServerType.MEMGRAPH else "id"
            result = session.run(
                f"CREATE (h:Human $props) RETURN {operator}(h)",
                {"props": {"name": "John"}},
            )
            identifier = result.value()[0]

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(element_id(aliased_human), identifier)
            compiled_expression = cast(ComparisonExpression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestIdExpressions:
    @pytest.mark.integration
    def test_id_query(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated id queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            result = session.run(
                "CREATE (h:Human $props) RETURN id(h)",
                {"props": {"name": "John"}},
            )
            identifier = result.value()[0]

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(id_(Human), identifier)
            compiled_expression = cast(ComparisonExpression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_id_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated id queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            result = session.run(
                "CREATE (h:Human $props) RETURN id(h)",
                {"props": {"name": "John"}},
            )
            identifier = result.value()[0]

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(id_(aliased_human), identifier)
            compiled_expression = cast(ComparisonExpression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"
