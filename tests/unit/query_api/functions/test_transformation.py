# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import cast

import pytest

from loomi.constants import ServerType
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.protocols import CompiledDescriptor
from loomi.query_api.functions.transformation import (
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


class Person(Node):
    name: str
    age: int


@pytest.fixture
def compilation_context():
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(Person)

    return ctx


class TestTail:
    def test_tail_returns_valid_descriptor(self, compilation_context):
        db_function = tail(Person.name)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "tail({variable}.name)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestAbs:
    def test_abs_returns_valid_descriptor(self, compilation_context):
        db_function = abs_(Person.age)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "abs({variable}.age)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestCeil:
    def test_ceil_returns_valid_descriptor(self, compilation_context):
        db_function = ceil(Person.age)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "ceil({variable}.age)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestFloor:
    def test_floor_returns_valid_descriptor(self, compilation_context):
        db_function = floor(Person.age)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "floor({variable}.age)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestRound:
    def test_round_returns_valid_descriptor(self, compilation_context):
        db_function = round_(Person.age)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "round({variable}.age)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestLtrim:
    def test_ltrim_returns_valid_descriptor(self, compilation_context):
        db_function = ltrim(Person.name)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "ltrim({variable}.name)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestRtrim:
    def test_rtrim_returns_valid_descriptor(self, compilation_context):
        db_function = rtrim(Person.name)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "rtrim({variable}.name)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestTrim:
    def test_trim_returns_valid_descriptor(self, compilation_context):
        db_function = trim(Person.name)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "trim({variable}.name)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestToLower:
    def test_to_lower_returns_valid_descriptor(self, compilation_context):
        db_function = to_lower(Person.name)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "toLower({variable}.name)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestToUpper:
    def test_to_upper_returns_valid_descriptor(self, compilation_context):
        db_function = to_upper(Person.name)
        compiled = cast(CompiledDescriptor, db_function._compile_db_function(compilation_context))

        assert compiled.variable_path == "toUpper({variable}.name)"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0
