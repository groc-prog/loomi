# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import List, LiteralString, cast

import neo4j
import pytest

from loomi.graph.node import Node
from loomi.query.alias import create_alias
from loomi.query.db_function import DbFunction
from loomi.query.expressions import QueryCompilationContext, QueryExpression
from loomi.query.functions.comparison import equals, in_
from loomi.query.functions.identity import element_id
from loomi.query.functions.transformation import (
    abs_,
    ceil,
    floor,
    ltrim,
    round_,
    rtrim,
    tail,
    to_lower,
    to_upper,
    trim,
)
from tests.fixtures.db import NEO4J_DRIVER_SPEC, DriverSpec, driver_spec, sync_cleanup, sync_driver


class Human(Node):
    name: str
    age: int
    hobbies: List[str]


aliased_human = create_alias(Human, "human")


class TestTailDbFunction:
    @pytest.mark.integration
    def test_tail_db_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated tail queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Running", "Video Games"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Running", "Reading"]}},
            )

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(tail(Human.hobbies), ["Video Games"])
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_tail_db_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated tail queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = in_(Human.name, tail(["Jane", "John"]))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_tail_db_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated tail queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "John", "hobbies": ["Running", "Video Games"]}},
            )
            session.run(
                "CREATE (:Human $props)",
                {"props": {"name": "Jane", "hobbies": ["Running", "Reading"]}},
            )

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(tail(Human.hobbies), tail(["Running", "Video Games"]))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestAbsDbFunction:
    @pytest.mark.integration
    def test_to_abs_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated abs queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": -24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": -20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(abs_(Human.age), 24)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_abs_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated abs queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.age, abs_(-24))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_abs_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated abs queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": -24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": -20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(abs_(Human.age), abs_(-24))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestCeilDbFunction:
    @pytest.mark.integration
    def test_to_ceil_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ceil queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 23.3}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20.5}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(ceil(Human.age), 24)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_ceil_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ceil queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.age, ceil(23.3))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_ceil_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ceil queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 23.3}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(ceil(Human.age), ceil(23.6))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestFloorDbFunction:
    @pytest.mark.integration
    def test_to_floor_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated floor queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24.3}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20.5}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(floor(Human.age), 24)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_floor_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated floor queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.age, floor(24.3))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_floor_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated floor queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24.3}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(floor(Human.age), floor(24.6))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestRoundDbFunction:
    @pytest.mark.integration
    def test_to_round_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated round queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24.3}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20.5}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(round_(Human.age), 24)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_round_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated round queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.age, round_(24.3))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_round_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated round queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John", "age": 24.3}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane", "age": 20}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(round_(Human.age), round_(24.4))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestLtrimDbFunction:
    @pytest.mark.integration
    def test_to_ltrim_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ltrim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "  John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(ltrim(Human.name), "John")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_to_ltrim_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ltrim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, ltrim("    John"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_to_ltrim_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated ltrim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "   John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(ltrim(Human.name), ltrim("     John"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1


class TestRTrimDbFunction:
    @pytest.mark.integration
    def test_to_rtrim_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated rtrim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John   "}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(rtrim(Human.name), "John")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_to_rtrim_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated rtrim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, rtrim("John    "))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_to_rtrim_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated rtrim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John   "}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(rtrim(Human.name), rtrim("John     "))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1


class TestTrimDbFunction:
    @pytest.mark.integration
    def test_to_trim_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated trim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "  John   "}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(trim(Human.name), "John")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_to_trim_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated trim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, trim("      John    "))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_to_trim_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated trim queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "  John   "}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(trim(Human.name), trim("   John     "))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1


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


class TestToUpperDbFunction:
    @pytest.mark.integration
    def test_to_upper_db_function_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated toLower queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(to_upper(Human.name), "JOHN")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"

    @pytest.mark.integration
    def test_to_upper_db_function_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated toLower queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "JOHN"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "JANE"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, to_upper("John"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "JOHN"

    @pytest.mark.integration
    def test_to_upper_db_function_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated toLower queries from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})
            session.run("CREATE (:Human $props)", {"props": {"name": "Jane"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(to_upper(Human.name), to_upper("John"))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
            assert entities[0]["name"] == "John"


class TestNestedDbFunctions:
    @pytest.mark.integration
    def test_allows_nesting_db_functions_with_variable(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated queries with nested DB functions from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "   John "}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(trim(to_upper(Human.name)), "JOHN")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_allows_nesting_db_functions_with_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated queries with nested DB functions from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "JOHN"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(Human.name, trim(to_upper("  John    ")))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_allows_nesting_db_functions_with_variable_and_parameter(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the generated queries with nested DB functions from the helper fn can be run by the driver."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(trim(to_upper(Human.name)), trim(to_upper("   John  ")))
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1


class TestDbFunctionWithEntityDescriptor:
    @pytest.mark.integration
    def test_db_functions_with_wrapped_entity_descriptor(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that db functions used with entity descriptors are compiled correctly."""
        with sync_driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(driver_spec.name)
            ctx.add_model(Human)
            expression = equals(trim(element_id(Human)), trim("element-id"))
            compiled_expression = expression._compile(ctx)

            # We only check if it can compile since I cant think of a better test case right now
            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)


class TestDbFunctionWithArgs:
    @pytest.mark.integration
    def test_db_function_with_args_with_variable(self):
        """Verify that the DB functions can use additional arguments."""
        driver = neo4j.GraphDatabase.driver(
            cast(str, NEO4J_DRIVER_SPEC.uri),
            auth=(cast(str, NEO4J_DRIVER_SPEC.user), cast(str, NEO4J_DRIVER_SPEC.pwd)),
        )
        sync_cleanup(driver, NEO4J_DRIVER_SPEC.name)

        transformer = DbFunction(Human.name, "rtrim({variable_or_parameter}, {arg0})", ["'n'"])

        with driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(NEO4J_DRIVER_SPEC.name)
            ctx.add_model(Human)
            expression = equals(transformer, "Joh")
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_db_function_with_args_with_parameter(self):
        """Verify that the DB functions can use additional arguments."""
        driver = neo4j.GraphDatabase.driver(
            cast(str, NEO4J_DRIVER_SPEC.uri),
            auth=(cast(str, NEO4J_DRIVER_SPEC.user), cast(str, NEO4J_DRIVER_SPEC.pwd)),
        )
        sync_cleanup(driver, NEO4J_DRIVER_SPEC.name)

        transformer = DbFunction("John", "rtrim({variable_or_parameter}, {arg0})", ["'n'"])

        with driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "Joh"}})

            ctx = QueryCompilationContext(NEO4J_DRIVER_SPEC.name)
            ctx.add_model(Human)
            expression = equals(Human.name, transformer)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1

    @pytest.mark.integration
    def test_db_function_with_args_with_variable_and_parameter(self):
        """Verify that the DB functions can use additional arguments."""
        driver = neo4j.GraphDatabase.driver(
            cast(str, NEO4J_DRIVER_SPEC.uri),
            auth=(cast(str, NEO4J_DRIVER_SPEC.user), cast(str, NEO4J_DRIVER_SPEC.pwd)),
        )
        sync_cleanup(driver, NEO4J_DRIVER_SPEC.name)

        transformer_parameter = DbFunction(
            "John", "rtrim({variable_or_parameter}, {arg0})", ["'n'"]
        )
        transformer_variable = DbFunction(
            Human.name, "rtrim({variable_or_parameter}, {arg0})", ["'n'"]
        )

        with driver.session() as session:
            session.run("CREATE (:Human $props)", {"props": {"name": "John"}})

            ctx = QueryCompilationContext(NEO4J_DRIVER_SPEC.name)
            ctx.add_model(Human)
            expression = equals(transformer_variable, transformer_parameter)
            compiled_expression = expression._compile(ctx)

            query = f"MATCH ({ctx.get_variable(Human)}:Human) WHERE {compiled_expression} RETURN {ctx.get_variable(Human)}"
            result = session.run(cast(LiteralString, query), ctx.parameters)

            entities = result.value()
            assert len(entities) == 1
