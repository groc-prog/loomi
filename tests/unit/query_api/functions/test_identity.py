# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import cast

import pytest

from loomi.constants import ServerType
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.protocols import CompiledDescriptor
from loomi.query_api.functions.identity import element_id, id_


class Person(Node):
    name: str
    age: int


@pytest.fixture
def compilation_context():
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(Person)

    return ctx


class TestElementId:
    def test_element_id_returns_valid_descriptor(self, compilation_context):
        expression = element_id(Person)
        compiled = cast(CompiledDescriptor, expression._compile_descriptor(compilation_context))

        assert compiled.variable_path == "elementId({variable})"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0


class TestId:
    def test_id_returns_valid_descriptor(self, compilation_context):
        expression = id_(Person)
        compiled = cast(CompiledDescriptor, expression._compile_descriptor(compilation_context))

        assert compiled.variable_path == "id({variable})"
        assert compiled.variable == "v0"
        assert len(compilation_context.get_parameters()) == 0
