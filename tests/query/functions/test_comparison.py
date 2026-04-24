# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import LiteralString, cast

import neo4j
import pytest
from pydantic import BaseModel

from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.expressions import CompilationContext, Expression
from loomi.query.functions.comparison import (
    and_,
    contains,
    cypher,
    ends_with,
    equals,
    greater_than,
    greater_than_or_equal,
    in_,
    is_not_null,
    is_null,
    less_than,
    less_than_or_equal,
    not_,
    not_equals,
    or_,
    regex,
    starts_with,
    xor,
)
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class Human(Node):
    name: str
    age: int


aliased_human = create_alias(Human, "human")


class TestEqualsExpression:
    @pytest.mark.integration
    def test_eq_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated EQ queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, "John")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_eq_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated EQ queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = equals(aliased_human.name, "John")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_eq_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated EQ queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.name == "John"
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestNotEqualsExpression:
    @pytest.mark.integration
    def test_neq_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated NEQ queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = not_equals(Human.name, "Jane")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_neq_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated NEQ queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = not_equals(aliased_human.name, "Jane")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_neq_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated NEQ queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.name != "Jane"
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestGreaterExpression:
    @pytest.mark.integration
    def test_gt_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated GT queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = greater_than(Human.age, 23)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 24

    @pytest.mark.integration
    def test_gt_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated GT queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = greater_than(aliased_human.age, 23)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 24

    @pytest.mark.integration
    def test_gt_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated GT queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age > 23
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 24


class TestGreaterOrEqualsExpression:
    @pytest.mark.integration
    def test_gte_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated GTE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = greater_than_or_equal(Human.age, 24)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 24

    @pytest.mark.integration
    def test_gte_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated GTE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = greater_than_or_equal(aliased_human.age, 24)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 24

    @pytest.mark.integration
    def test_gte_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated GTE queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age >= 24
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 24


class TestLessExpression:
    @pytest.mark.integration
    def test_lt_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated LT queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = less_than(Human.age, 23)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 22

    @pytest.mark.integration
    def test_lt_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated LT queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = less_than(aliased_human.age, 23)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 22

    @pytest.mark.integration
    def test_lt_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated LT queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age < 23
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 22


class TestLessOrEqualsExpression:
    @pytest.mark.integration
    def test_lte_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated LTE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = less_than_or_equal(Human.age, 22)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 22

    @pytest.mark.integration
    def test_lte_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated LTE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = less_than_or_equal(aliased_human.age, 22)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 22

    @pytest.mark.integration
    def test_lte_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated LTE queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age <= 22
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["age"] == 22


class TestNotExpression:
    @pytest.mark.integration
    def test_not_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated EQ queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = not_(equals(Human.name, "Jane"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_not_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated EQ queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = not_(equals(aliased_human.name, "Jane"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_not_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated EQ queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = ~(Human.name == "Jane")
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestIsNullExpression:
    @pytest.mark.integration
    def test_is_null_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated IS NULL queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": None}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = is_null(Human.name)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] is None

    @pytest.mark.integration
    def test_is_null_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated IS NULL queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": None}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = is_null(aliased_human.name)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] is None


class TestIsNotNullExpression:
    @pytest.mark.integration
    def test_is_not_null_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated IS NOT NULL queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": None}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = is_not_null(Human.name)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_is_not_null_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated IS NOT NULL queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": None}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = is_not_null(aliased_human.name)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestInExpression:
    @pytest.mark.integration
    def test_in_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated IN queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = in_(Human.name, ["Monty", "John", "James"])
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_in_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated IN queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = in_(aliased_human.name, ["Monty", "John", "James"])
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestStartsWithExpression:
    @pytest.mark.integration
    def test_starts_with_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated STARTS WITH queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = starts_with(Human.name, "Jo")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_starts_with_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated STARTS WITH queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = starts_with(aliased_human.name, "Jo")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestEndsWithExpression:
    @pytest.mark.integration
    def test_ends_with_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ENDS WITH queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = ends_with(Human.name, "hn")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_ends_with_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ENDS WITH queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = ends_with(aliased_human.name, "hn")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestContainsExpression:
    @pytest.mark.integration
    def test_contains_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated CONTAINS queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = contains(Human.name, "o")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_contains_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated CONTAINS queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = contains(aliased_human.name, "o")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestRegexExpression:
    @pytest.mark.integration
    def test_regex_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated REGEX queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = regex(Human.name, ".*hn")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_regex_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated REGEX queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = regex(aliased_human.name, ".*hn")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestAndExpressions:
    @pytest.mark.integration
    def test_and_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated AND queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = and_(equals(Human.name, "John"), equals(Human.age, 24))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_and_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated AND queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = and_(equals(aliased_human.name, "John"), equals(aliased_human.age, 24))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_and_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated AND queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = (Human.name == "John") & (Human.age == 24)
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestNestedAndExpressions:
    @pytest.mark.integration
    def test_nested_and_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated nested AND queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = and_(
                and_(equals(Human.name, "John"), less_than(Human.age, 30)),
                greater_than(Human.age, 20),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_and_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested AND queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = and_(
                and_(equals(aliased_human.name, "John"), less_than(aliased_human.age, 30)),
                greater_than(aliased_human.age, 20),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_and_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested AND queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = ((Human.name == "John") & (Human.age > 20)) & (Human.age < 30)
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_and_query_with_other_logical_expression(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested AND queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = and_(
                or_(equals(Human.name, "John"), equals(Human.age, 30)),
                greater_than(Human.age, 20),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestOrExpressions:
    @pytest.mark.integration
    def test_or_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated OR queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = or_(equals(Human.name, "John"), equals(Human.age, 30))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_or_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated OR queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = or_(equals(aliased_human.name, "John"), equals(aliased_human.age, 30))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_or_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated OR queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = (Human.name == "John") | (Human.age == 30)
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestNestedOrExpressions:
    @pytest.mark.integration
    def test_nested_or_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated nested OR queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = or_(
                or_(equals(Human.name, "John"), equals(Human.age, 30)), equals(Human.age, 40)
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_or_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested OR queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = or_(
                or_(equals(aliased_human.name, "John"), equals(aliased_human.age, 30)),
                equals(aliased_human.age, 40),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_or_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested OR queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = ((Human.name == "John") | (Human.age == 30)) | (Human.age == 40)
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_or_query_with_other_logical_expression(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested OR queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = or_(
                and_(equals(Human.name, "John"), less_than(Human.age, 30)),
                equals(Human.age, 20),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestXorExpressions:
    @pytest.mark.integration
    def test_xor_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated XOR queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = xor(equals(Human.name, "John"), equals(Human.age, 30))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_xor_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated XOR queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = xor(equals(aliased_human.name, "John"), equals(aliased_human.age, 30))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_xor_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated XOR queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = (Human.name == "John") ^ (Human.age == 30)
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestNestedXorExpressions:
    @pytest.mark.integration
    def test_nested_xor_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated nested XOR queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = xor(
                xor(equals(Human.name, "John"), equals(Human.age, 30)), equals(Human.age, 40)
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_xor_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested XOR queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = xor(
                xor(equals(aliased_human.name, "John"), equals(aliased_human.age, 30)),
                equals(aliased_human.age, 40),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_xor_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested XOR queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 22}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = ((Human.name == "John") ^ (Human.age == 30)) ^ (Human.age == 40)
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_nested_xor_query_with_other_logical_expression(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated nested XOR queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 24}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = xor(
                and_(equals(Human.name, "John"), less_than(Human.age, 30)),
                equals(Human.age, 20),
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestCustomExpression:
    @pytest.mark.integration
    def test_in_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated custom queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = cypher(
                "{human}.name IN {list_values}",
                {"human": Human},
                {"list_values": ["Monty", "John", "James"]},
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_in_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated custom queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = cypher(
                "{human}.name IN {list_values}",
                {"human": aliased_human},
                {"list_values": ["Monty", "John", "James"]},
            )
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(aliased_human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"
