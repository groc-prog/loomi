# pylint: disable=unused-import, redefined-outer-name, unused-argument, line-too-long, unused-variable, comparison-with-callable

import re
from typing import Any, List

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import (
    CompoundExpression,
    CustomCypherExpression,
    Expression,
    InvertExpression,
)
from loomi.query_api._core.protocols import CompiledExpression
from loomi.query_api.functions.arithmetic import add, divide, multiply
from loomi.query_api.functions.collection import any_, single
from loomi.query_api.functions.comparison import and_, cypher, equals, not_, or_
from loomi.query_api.functions.transformation import ltrim, rtrim, to_lower, to_upper


class NestedField(BaseModel):
    field: Any
    other_field: Any


class NodeModel(Node):
    field: Any
    list_field: List[Any]
    nested_list: List[NestedField]
    nested: NestedField


@pytest.fixture
def compilation_ctx():
    ctx = CompilationContext(ServerType.NEO4J)
    ctx.add_model(NodeModel)

    return ctx


class TestCustomExpression:
    def test_custom_expression_without_parameters(self, compilation_ctx):
        expression = cypher("{model}.foo IS NOT NONE", {"model": NodeModel}, {})
        assert isinstance(expression, CustomCypherExpression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.foo IS NOT NONE"

    def test_custom_expression_with_parameters(self, compilation_ctx):
        expression = cypher("{model}.foo = {arg}", {"model": NodeModel}, {"arg": "bar"})
        assert isinstance(expression, CustomCypherExpression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.foo = $p0"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == "bar"
