# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable


import pytest

from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api.functions.comparison import (
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


class Person(Node):
    name: str
    age: int


@pytest.fixture
def compilation_context():
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(Person)

    return ctx


class TestEquals:
    def test_equals_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            equals("invalid_value", 22)  # type: ignore

    def test_equals_returns_valid_expression(self, compilation_context):
        expression = equals(Person.age, 22)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age = $p0"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestNotEquals:
    def test_not_equals_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            not_equals("invalid_value", 22)  # type: ignore

    def test_not_equals_returns_valid_expression(self, compilation_context):
        expression = not_equals(Person.age, 22)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age <> $p0"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestGreaterThan:
    def test_greater_than_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            greater_than("invalid_value", 22)  # type: ignore

    def test_greater_than_returns_valid_expression(self, compilation_context):
        expression = greater_than(Person.age, 22)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age > $p0"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestGreaterThanOrEqual:
    def test_greater_than_or_equal_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            greater_than_or_equal("invalid_value", 22)  # type: ignore

    def test_greater_than_or_equal_returns_valid_expression(self, compilation_context):
        expression = greater_than_or_equal(Person.age, 22)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age >= $p0"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestLessThan:
    def test_less_than_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            less_than("invalid_value", 22)  # type: ignore

    def test_less_than_returns_valid_expression(self, compilation_context):
        expression = less_than(Person.age, 22)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age < $p0"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestLessThanOrEqual:
    def test_less_than_or_equal_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            less_than_or_equal("invalid_value", 22)  # type: ignore

    def test_less_than_or_equal_returns_valid_expression(self, compilation_context):
        expression = less_than_or_equal(Person.age, 22)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age <= $p0"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestNot:
    def test_not_returns_valid_expression(self, compilation_context):
        expression = not_(equals(Person.age, 22))
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "NOT(v0.age = $p0)"
        assert compilation_context.get_parameters() == {"p0": 22}


class TestAnd:
    def test_and_returns_valid_expression(self, compilation_context):
        expression = and_(greater_than(Person.age, 22), less_than(Person.age, 30))

        assert expression.to_query_string(compilation_context) == "v0.age > $p0 AND v0.age < $p1"
        assert compilation_context.get_parameters() == {"p0": 22, "p1": 30}


class TestOr:
    def test_or_returns_valid_expression(self, compilation_context):
        expression = or_(equals(Person.age, 22), equals(Person.age, 30))

        assert expression.to_query_string(compilation_context) == "v0.age = $p0 OR v0.age = $p1"
        assert compilation_context.get_parameters() == {"p0": 22, "p1": 30}


class TestXor:
    def test_xor_returns_valid_expression(self, compilation_context):
        expression = xor(equals(Person.age, 22), equals(Person.age, 30))

        assert expression.to_query_string(compilation_context) == "v0.age = $p0 XOR v0.age = $p1"
        assert compilation_context.get_parameters() == {"p0": 22, "p1": 30}


class TestIsNull:
    def test_is_null_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Descriptor must be a valid field descriptor. Expected CompilableDescriptor, got invalid_value",
        ):
            is_null("invalid_value")  # type: ignore

    def test_is_null_returns_valid_expression(self, compilation_context):
        expression = is_null(Person.age)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age IS NULL"
        assert compilation_context.get_parameters() == {"p0": None}


class TestIsNotNull:
    def test_is_not_null_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Descriptor must be a valid field descriptor. Expected CompilableDescriptor, got invalid_value",
        ):
            is_not_null("invalid_value")  # type: ignore

    def test_is_not_null_returns_valid_expression(self, compilation_context):
        expression = is_not_null(Person.age)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age IS NOT NULL"
        assert compilation_context.get_parameters() == {"p0": None}


class TestIn:
    def test_in_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            in_("invalid_value", [2, 3, 4])  # type: ignore

    def test_in_returns_valid_expression(self, compilation_context):
        expression = in_(Person.age, [2, 3, 4])
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age IN $p0"
        assert compilation_context.get_parameters() == {"p0": [2, 3, 4]}


class TestStartsWith:
    def test_starts_with_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            starts_with("invalid_value", "foo")  # type: ignore

    def test_starts_with_returns_valid_expression(self, compilation_context):
        expression = starts_with(Person.name, "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name STARTS WITH $p0"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestEndsWith:
    def test_ends_with_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            ends_with("invalid_value", "foo")  # type: ignore

    def test_ends_with_returns_valid_expression(self, compilation_context):
        expression = ends_with(Person.name, "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name ENDS WITH $p0"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestContains:
    def test_contains_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            contains("invalid_value", "foo")  # type: ignore

    def test_contains_returns_valid_expression(self, compilation_context):
        expression = contains(Person.name, "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name CONTAINS $p0"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestRegex:
    def test_regex_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            regex("invalid_value", "foo")  # type: ignore

    def test_regex_returns_valid_expression(self, compilation_context):
        expression = regex(Person.name, "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.name =~ $p0"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestCypher:
    def test_cypher_returns_valid_expression(self, compilation_context):
        expression = cypher(
            "{person}.age >= {min_age} AND {person}.age <= {max_age}",
            {"person": Person},
            {"min_age": 22, "max_age": 30},
        )
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age >= $p0 AND v0.age <= $p1"
        assert compilation_context.get_parameters() == {"p0": 22, "p1": 30}
