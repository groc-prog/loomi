# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import datetime
from typing import List, cast

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import CompoundExpression, Expression
from loomi.query_api.functions.collection import any_, single
from loomi.query_api.functions.comparison import and_, cypher, equals, not_, or_, xor
from loomi.query_api.functions.transformation import to_lower, trim


class ObjectTimestamp(BaseModel):
    name: str
    timestamp: datetime.datetime


class PersonHobby(BaseModel):
    name: str


class PersonMetadata(BaseModel):
    hobbies: List[PersonHobby]


class Person(Node):
    name: str
    age: int
    active: bool
    metadata: PersonMetadata
    timestamps: List[ObjectTimestamp]


@pytest.fixture
def compilation_context():
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(Person)

    return ctx


class TestExpressionMagicMethods:
    def test_expression_invert_magic_method(self, compilation_context):
        expression = ~(Person.active == True)
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "NOT(v0.active = $p0)"
        assert compilation_context.get_parameters() == {"p0": True}

    def test_expression_and_magic_method(self, compilation_context):
        expression = (Person.name == "Alice") & (Person.active == True)
        query_string = cast(CompoundExpression, expression).to_query_string(compilation_context)

        assert query_string == "v0.name = $p0 AND v0.active = $p1"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": True}

    def test_expression_or_magic_method(self, compilation_context):
        expression = (Person.name == "Alex") | (Person.age == 40)
        query_string = cast(CompoundExpression, expression).to_query_string(compilation_context)

        assert query_string == "v0.name = $p0 OR v0.age = $p1"
        assert compilation_context.get_parameters() == {"p0": "Alex", "p1": 40}

    def test_expression_xor_magic_method(self, compilation_context):
        expression = (Person.name == "Alice") ^ (Person.age == 40)
        query_string = cast(CompoundExpression, expression).to_query_string(compilation_context)

        assert query_string == "v0.name = $p0 XOR v0.age = $p1"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 40}


class TestExpressionWithDbFunction:
    def test_expression_with_db_function_wrapping_value(self, compilation_context):
        expression = equals(Person.name, to_lower("Alice"))
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name = toLower($p0)"
        assert compilation_context.get_parameters() == {"p0": "Alice"}

    def test_expression_with_db_function_wrapping_descriptor(self, compilation_context):
        expression = equals(to_lower(Person.name), "Alice")
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "toLower(v0.name) = $p0"
        assert compilation_context.get_parameters() == {"p0": "Alice"}

    def test_expression_with_db_function_wrapping_value_and_descriptor(self, compilation_context):
        expression = equals(to_lower(Person.name), to_lower("Alice"))
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "toLower(v0.name) = toLower($p0)"
        assert compilation_context.get_parameters() == {"p0": "Alice"}

    def test_expression_with_nested_db_functions_wrapping_value(self, compilation_context):
        expression = equals(Person.name, to_lower(trim("Alice")))
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name = toLower(trim($p0))"
        assert compilation_context.get_parameters() == {"p0": "Alice"}

    def test_expression_with_nested_db_functions_wrapping_descriptor(self, compilation_context):
        expression = equals(to_lower(trim(Person.name)), "Alice")
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "toLower(trim(v0.name)) = $p0"
        assert compilation_context.get_parameters() == {"p0": "Alice"}

    def test_expression_with_nested_db_functions_wrapping_value_and_descriptor(
        self, compilation_context
    ):
        expression = equals(to_lower(trim(Person.name)), to_lower(trim("Alice")))
        compiled = cast(Expression, expression)._compile_expression(compilation_context)

        assert compiled.to_query_string() == "toLower(trim(v0.name)) = toLower(trim($p0))"
        assert compilation_context.get_parameters() == {"p0": "Alice"}


class TestCompoundExpressionMagicMethods:
    def test_compound_expression_and_magic_method(self, compilation_context):
        expression = xor(equals(Person.name, "Alice"), equals(Person.age, 50)) & equals(
            Person.active, True
        )
        query_string = expression.to_query_string(compilation_context)

        assert query_string == "(v0.name = $p0 XOR v0.age = $p1) AND v0.active = $p2"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 50, "p2": True}

    def test_compound_expression_and_magic_method_combines_all_conditions_into_same_operator_if_all_operators_identical(
        self, compilation_context
    ):
        expression = and_(equals(Person.name, "Alice"), equals(Person.age, 30)) & equals(
            Person.active, True
        )
        query_string = expression.to_query_string(compilation_context)

        assert query_string == "v0.name = $p0 AND v0.age = $p1 AND v0.active = $p2"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 30, "p2": True}

    def test_compound_expression_or_magic_method(self, compilation_context):
        expression = and_(equals(Person.name, "Alice"), equals(Person.age, 20)) | equals(
            Person.active, False
        )
        query_string = expression.to_query_string(compilation_context)

        assert query_string == "(v0.name = $p0 AND v0.age = $p1) OR v0.active = $p2"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 20, "p2": False}

    def test_compound_expression_or_magic_method_combines_all_conditions_into_same_operator_if_all_operators_identical(
        self, compilation_context
    ):
        expression = or_(equals(Person.name, "Thomas"), equals(Person.age, 40)) | equals(
            Person.active, False
        )
        query_string = expression.to_query_string(compilation_context)

        assert query_string == "v0.name = $p0 OR v0.age = $p1 OR v0.active = $p2"
        assert compilation_context.get_parameters() == {"p0": "Thomas", "p1": 40, "p2": False}

    def test_compound_expression_xor_magic_method(self, compilation_context):
        expression = and_(equals(Person.name, "Alice"), equals(Person.age, 20)) ^ equals(
            Person.active, False
        )
        query_string = expression.to_query_string(compilation_context)

        assert query_string == "(v0.name = $p0 AND v0.age = $p1) XOR v0.active = $p2"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 20, "p2": False}

    def test_compound_expression_xor_magic_method_combines_all_conditions_into_same_operator_if_all_operators_identical(
        self, compilation_context
    ):
        expression = xor(equals(Person.name, "Thomas"), equals(Person.age, 50)) ^ equals(
            Person.active, False
        )
        query_string = expression.to_query_string(compilation_context)

        assert query_string == "v0.name = $p0 XOR v0.age = $p1 XOR v0.active = $p2"
        assert compilation_context.get_parameters() == {"p0": "Thomas", "p1": 50, "p2": False}

    def test_compound_expression_invert_magic_method(self, compilation_context):
        expression = ~(
            and_(equals(Person.name, "Alice"), equals(Person.age, 30)) & equals(Person.active, True)
        )
        compiled = cast(Expression, expression)._compile_expression(compilation_context)
        query_string = compiled.to_query_string()

        assert query_string == "NOT(v0.name = $p0 AND v0.age = $p1 AND v0.active = $p2)"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 30, "p2": True}


class TestCompoundExpressionNestedPathOptimization:
    def test_compound_expression_optimizes_nested_paths(self, compilation_context):
        expression = and_(
            or_(
                equals(any_(Person.metadata.hobbies).name, "Fishing"),
                equals(any_(Person.metadata.hobbies).name, "Running"),
            ),
            equals(single(Person.timestamps).name, "died_at"),
        )
        query_string = expression.to_query_string(compilation_context)

        assert (
            query_string
            == "(any(v1 IN v0.metadata.hobbies WHERE v1.name = $p0 OR v1.name = $p1)) AND single(v3 IN v0.timestamps WHERE v3.name = $p2)"
        )
        assert compilation_context.get_parameters() == {
            "p0": "Fishing",
            "p1": "Running",
            "p2": "died_at",
        }


class TestInvertExpression:
    def test_invert_expression(self, compilation_context):
        expression = not_(equals(Person.name, "Alice"))
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "NOT(v0.name = $p0)"
        assert compilation_context.get_parameters() == {"p0": "Alice"}

    def test_invert_expression_with_nested_compound_expression(self, compilation_context):
        expression = not_(and_(equals(Person.name, "Alice"), equals(Person.age, 30)))
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "NOT(v0.name = $p0 AND v0.age = $p1)"
        assert compilation_context.get_parameters() == {"p0": "Alice", "p1": 30}


class TestCustomCypherExpression:
    def test_custom_cypher(self, compilation_context):
        expression = cypher(
            "{person}.name IN {list_values}",
            {"person": Person},
            {"list_values": ["Monty", "John", "James"]},
        )
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name IN $p0"
        assert compilation_context.get_parameters() == {"p0": ["Monty", "John", "James"]}
