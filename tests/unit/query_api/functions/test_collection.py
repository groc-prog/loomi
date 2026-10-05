# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import List, cast

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api.functions.collection import all_, any_, none, single
from loomi.query_api.functions.comparison import equals


class Person(Node):
    items: List[str]


@pytest.fixture
def compilation_context():
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(Person)

    return ctx


class TestAll:
    def test_all_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Descriptor must be a valid field descriptor. Expected FieldDescriptor, got invalid_value",
        ):
            all_("invalid_value")  # type: ignore

    def test_all_returns_valid_expression(self, compilation_context):
        expression = equals(all_(Person.items), "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "all(v1 IN v0.items WHERE v1 = $p0)"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestAny:
    def test_any_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Descriptor must be a valid field descriptor. Expected FieldDescriptor, got invalid_value",
        ):
            any_("invalid_value")  # type: ignore

    def test_any_returns_valid_expression(self, compilation_context):
        expression = equals(any_(Person.items), "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "any(v1 IN v0.items WHERE v1 = $p0)"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestNone:
    def test_none_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Descriptor must be a valid field descriptor. Expected FieldDescriptor, got invalid_value",
        ):
            none("invalid_value")  # type: ignore

    def test_none_returns_valid_expression(self, compilation_context):
        expression = equals(none(Person.items), "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "none(v1 IN v0.items WHERE v1 = $p0)"
        assert compilation_context.get_parameters() == {"p0": "foo"}


class TestSingle:
    def test_single_raises_when_invalid_descriptor_or_db_function_is_provided(self):
        with pytest.raises(
            QueryError,
            match="Descriptor must be a valid field descriptor. Expected FieldDescriptor, got invalid_value",
        ):
            single("invalid_value")  # type: ignore

    def test_single_returns_valid_expression(self, compilation_context):
        expression = equals(single(Person.items), "foo")
        compiled = expression._compile_expression(compilation_context)

        assert compiled.to_query_string() == "single(v1 IN v0.items WHERE v1 = $p0)"
        assert compilation_context.get_parameters() == {"p0": "foo"}
