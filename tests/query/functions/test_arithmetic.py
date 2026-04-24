# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import LiteralString, cast

import neo4j
import pytest

from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.expressions import CompilationContext, Expression
from loomi.query.functions.arithmetic import (
    add,
    divide,
    modulo,
    multiply,
    pow_,
    reflected_add,
    reflected_divide,
    reflected_modulo,
    reflected_multiply,
    reflected_pow,
    reflected_subtract,
    subtract,
)
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class Human(Node):
    name: str
    age: int


aliased_human = create_alias(Human, "human")


class TestAddExpression:
    @pytest.mark.integration
    def test_add_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ADD queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = add(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 22

    @pytest.mark.integration
    def test_add_query_with_aliased_model(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ADD queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = add(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 22

    @pytest.mark.integration
    def test_add_query_with_magic_method(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated ADD queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age + 2
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 22


class TestReflectedAddExpression:
    @pytest.mark.integration
    def test_reflected_add_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated reflected ADD queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = reflected_add(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 22

    @pytest.mark.integration
    def test_reflected_add_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected ADD queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = reflected_add(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 22

    @pytest.mark.integration
    def test_reflected_add_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected ADD queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = 2 + Human.age
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 22


class TestSubtractExpression:
    @pytest.mark.integration
    def test_subtract_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated SUBTRACT queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = subtract(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 18

    @pytest.mark.integration
    def test_subtract_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated SUBTRACT queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = subtract(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 18

    @pytest.mark.integration
    def test_subtract_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated SUBTRACT queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age - 2
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 18


class TestReflectedSubtractExpression:
    @pytest.mark.integration
    def test_reflected_subtract_query_with_fn(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected SUBTRACT queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = reflected_subtract(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == -18

    @pytest.mark.integration
    def test_reflected_subtract_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected SUBTRACT queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = reflected_subtract(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == -18

    @pytest.mark.integration
    def test_reflected_subtract_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected SUBTRACT queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = 2 - Human.age
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == -18


class TestMultiplyExpression:
    @pytest.mark.integration
    def test_multiply_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated MULTIPLY queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = multiply(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 40

    @pytest.mark.integration
    def test_multiply_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated MULTIPLY queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = multiply(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 40

    @pytest.mark.integration
    def test_multiply_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated MULTIPLY queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age * 2
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 40


class TestReflectedMultiplyExpression:
    @pytest.mark.integration
    def test_reflected_multiply_query_with_fn(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected MULTIPLY queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = reflected_multiply(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 40

    @pytest.mark.integration
    def test_reflected_multiply_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected MULTIPLY queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = reflected_multiply(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 40

    @pytest.mark.integration
    def test_reflected_multiply_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected MULTIPLY queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = 2 * Human.age
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 40


class TestDivideExpression:
    @pytest.mark.integration
    def test_divide_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated DIVIDE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = divide(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 10

    @pytest.mark.integration
    def test_divide_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated DIVIDE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = divide(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 10

    @pytest.mark.integration
    def test_divide_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated DIVIDE queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age / 2
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 10


class TestReflectedDivideExpression:
    @pytest.mark.integration
    def test_reflected_divide_query_with_fn(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected DIVIDE queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = reflected_divide(Human.age, 2.0)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            #
            assert entities[0] == 0.1

    @pytest.mark.integration
    def test_reflected_divide_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected DIVIDE queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = reflected_divide(aliased_human.age, 2.0)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 0.1

    @pytest.mark.integration
    def test_reflected_divide_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected DIVIDE queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = 2.0 / Human.age
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 0.1


class TestModuloExpression:
    @pytest.mark.integration
    def test_divide_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated MODULO queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = modulo(Human.age, 2.0)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 0.0

    @pytest.mark.integration
    def test_divide_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated MODULO queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = modulo(aliased_human.age, 2.0)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 0.0

    @pytest.mark.integration
    def test_divide_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated MODULO queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age % 2.0
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 0.0


class TestReflectedModuloExpression:
    @pytest.mark.integration
    def test_reflected_divide_query_with_fn(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected MODULO queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = reflected_modulo(Human.age, 2.0)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 2.0

    @pytest.mark.integration
    def test_reflected_divide_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected MODULO queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = reflected_modulo(aliased_human.age, 2.0)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 2.0

    @pytest.mark.integration
    def test_reflected_divide_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected MODULO queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = 2.0 % Human.age
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 2.0


class TestPowExpression:
    @pytest.mark.integration
    def test_divide_query_with_fn(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the generated MODULO queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = pow_(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 400

    @pytest.mark.integration
    def test_divide_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated POW queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = pow_(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 400

    @pytest.mark.integration
    def test_divide_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated POW queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = Human.age**2
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 400


class TestReflectedPowExpression:
    @pytest.mark.integration
    def test_reflected_divide_query_with_fn(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected POW queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = reflected_pow(Human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 1048576

    @pytest.mark.integration
    def test_reflected_divide_query_with_aliased_model(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected POW queries with aliased model can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(aliased_human)
            expression = reflected_pow(aliased_human.age, 2)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(aliased_human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 1048576

    @pytest.mark.integration
    def test_reflected_divide_query_with_magic_method(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated reflected POW queries from the magic method can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 20}})

            ctx = CompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = 2**Human.age
            compiled_expression = cast(Expression, expression)._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) RETURN {compiled_expression}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0] == 1048576
