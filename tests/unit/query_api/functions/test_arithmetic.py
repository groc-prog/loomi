# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import pytest

from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api.functions.arithmetic import (
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


class Person(Node):
    age: int


@pytest.fixture
def compilation_context():
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(Person)

    return ctx


class TestAdd:
    def test_add_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            add("invalid_value", 1)  # type: ignore

    def test_add_returns_valid_expression(self, compilation_context):
        expression = add(Person.age, 1)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age + $p0"
        assert compilation_context.get_parameters() == {"p0": 1}


class TestReflectedAdd:
    def test_reflected_add_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            reflected_add("invalid_value", 1)  # type: ignore

    def test_reflected_add_returns_valid_expression(self, compilation_context):
        expression = reflected_add(Person.age, 1)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "$p0 + v0.age"
        assert compilation_context.get_parameters() == {"p0": 1}


class TestSubtract:
    def test_subtract_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            subtract("invalid_value", 1)  # type: ignore

    def test_subtract_returns_valid_expression(self, compilation_context):
        expression = subtract(Person.age, 1)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age - $p0"
        assert compilation_context.get_parameters() == {"p0": 1}


class TestReflectedSubtract:
    def test_reflected_subtract_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            reflected_subtract("invalid_value", 1)  # type: ignore

    def test_reflected_subtract_returns_valid_expression(self, compilation_context):
        expression = reflected_subtract(Person.age, 1)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "$p0 - v0.age"
        assert compilation_context.get_parameters() == {"p0": 1}


class TestMultiply:
    def test_multiply_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            multiply("invalid_value", 2)  # type: ignore

    def test_multiply_returns_valid_expression(self, compilation_context):
        expression = multiply(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age * $p0"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestReflectedMultiply:
    def test_reflected_multiply_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            reflected_multiply("invalid_value", 2)  # type: ignore

    def test_reflected_multiply_returns_valid_expression(self, compilation_context):
        expression = reflected_multiply(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "$p0 * v0.age"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestDivide:
    def test_divide_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            divide("invalid_value", 2)  # type: ignore

    def test_divide_returns_valid_expression(self, compilation_context):
        expression = divide(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age / $p0"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestReflectedDivide:
    def test_reflected_divide_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            reflected_divide("invalid_value", 2)  # type: ignore

    def test_reflected_divide_returns_valid_expression(self, compilation_context):
        expression = reflected_divide(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "$p0 / v0.age"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestModulo:
    def test_modulo_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            modulo("invalid_value", 2)  # type: ignore

    def test_modulo_returns_valid_expression(self, compilation_context):
        expression = modulo(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age % $p0"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestReflectedModulo:
    def test_reflected_modulo_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            reflected_modulo("invalid_value", 2)  # type: ignore

    def test_reflected_modulo_returns_valid_expression(self, compilation_context):
        expression = reflected_modulo(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "$p0 % v0.age"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestPow:
    def test_pow_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            pow_("invalid_value", 2)  # type: ignore

    def test_pow_returns_valid_expression(self, compilation_context):
        expression = pow_(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "v0.age ^ $p0"
        assert compilation_context.get_parameters() == {"p0": 2}


class TestReflectedPow:
    def test_reflected_pow_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Value must be a valid field descriptor or db function. Expected CompilableDescriptor or CompilableDbFunction, got invalid_value",
        ):
            reflected_pow("invalid_value", 2)  # type: ignore

    def test_reflected_pow_returns_valid_expression(self, compilation_context):
        expression = reflected_pow(Person.age, 2)
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "$p0 ^ v0.age"
        assert compilation_context.get_parameters() == {"p0": 2}
