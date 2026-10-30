# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

from typing import Any, List

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import Expression
from loomi.query_api._core.protocols import CompiledExpression
from loomi.query_api.functions.collection import any_


class NestedField(BaseModel):
    field: Any


class NodeModel(Node):
    field: Any
    list_field: List[Any]
    nested_list: List[NestedField]
    nested: NestedField


@pytest.fixture
def compilation_ctx(server_type):
    ctx = CompilationContext(server_type)
    ctx.add_model(NodeModel)

    return ctx


@pytest.mark.parametrize("server_type", [ServerType.NEO4J, ServerType.MEMGRAPH])
class TestNodeExpressionsMagicMethods:

    class TestNodeExpressionEq:
        def test_node_expression_eq_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field = $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_node_expression_eq_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field = $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_node_expression_eq_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 = $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_node_expression_eq_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field = $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

    class TestNodeExpressionNe:
        def test_node_expression_ne_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field <> $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_node_expression_ne_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field <> $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_node_expression_ne_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 <> $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_node_expression_ne_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field <> $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

    class TestNodeExpressionGt:
        def test_node_expression_gt_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field > 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field > $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_gt_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field > 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field > $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_gt_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field > 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 > $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_gt_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field > 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field > $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionGte:
        def test_node_expression_gte_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field >= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field >= $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_gte_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field >= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field >= $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_gte_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field >= 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 >= $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_gte_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field >= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field >= $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionLt:
        def test_node_expression_lt_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field < 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field < $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_lt_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field < 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field < $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_lt_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field < 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 < $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_lt_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field < 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field < $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionLte:
        def test_node_expression_lte_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field <= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field <= $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_lte_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field <= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field <= $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_lte_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field <= 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 <= $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_lte_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field <= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field <= $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionAdd:
        def test_node_expression_add_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field + 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field + $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_add_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field + 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field + $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_add_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field + 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 + $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_add_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field + 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field + $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionRadd:
        def test_node_expression_radd_with_top_level_field(self, compilation_ctx):
            expression = 1 + NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 + v0.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_radd_with_nested_field(self, compilation_ctx):
            expression = 1 + NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 + v0.nested.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_radd_with_list_field(self, compilation_ctx):
            expression = 1 + NodeModel.list_field  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "$p0 + v1"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_radd_with_nested_list_field(self, compilation_ctx):
            expression = 1 + any_(NodeModel.nested_list).field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "$p0 + v1.field"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionSub:
        def test_node_expression_sub_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field - 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field - $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_sub_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field - 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field - $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_sub_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field - 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 - $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_sub_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field - 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field - $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionRsub:
        def test_node_expression_rsub_with_top_level_field(self, compilation_ctx):
            expression = 1 - NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 - v0.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_rsub_with_nested_field(self, compilation_ctx):
            expression = 1 - NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 - v0.nested.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_rsub_with_list_field(self, compilation_ctx):
            expression = 1 - NodeModel.list_field  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "$p0 - v1"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_node_expression_rsub_with_nested_list_field(self, compilation_ctx):
            expression = 1 - any_(NodeModel.nested_list).field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "$p0 - v1.field"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestNodeExpressionMul:
        def test_node_expression_mul_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field * 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field * $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_mul_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field * 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field * $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_mul_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field * 2  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 * $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_mul_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field * 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field * $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionRmul:
        def test_node_expression_rmul_with_top_level_field(self, compilation_ctx):
            expression = 2 * NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 * v0.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rmul_with_nested_field(self, compilation_ctx):
            expression = 2 * NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 * v0.nested.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rmul_with_list_field(self, compilation_ctx):
            expression = 2 * NodeModel.list_field  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "$p0 * v1"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rmul_with_nested_list_field(self, compilation_ctx):
            expression = 2 * any_(NodeModel.nested_list).field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "$p0 * v1.field"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionTruediv:
        def test_node_expression_truediv_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field / 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field / $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_truediv_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field / 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field / $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_truediv_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field / 2  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 / $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_truediv_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field / 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field / $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionRtruediv:
        def test_node_expression_rtruediv_with_top_level_field(self, compilation_ctx):
            expression = 2 / NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 / v0.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rtruediv_with_nested_field(self, compilation_ctx):
            expression = 2 / NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 / v0.nested.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rtruediv_with_list_field(self, compilation_ctx):
            expression = 2 / NodeModel.list_field  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "$p0 / v1"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rtruediv_with_nested_list_field(self, compilation_ctx):
            expression = 2 / any_(NodeModel.nested_list).field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "$p0 / v1.field"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionMod:
        def test_node_expression_mod_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field % 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field % $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_mod_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field % 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field % $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_mod_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field % 2  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 % $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_mod_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field % 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field % $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionRmod:
        def test_node_expression_rmod_with_top_level_field(self, compilation_ctx):
            expression = 2 % NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 % v0.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rmod_with_nested_field(self, compilation_ctx):
            expression = 2 % NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 % v0.nested.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rmod_with_list_field(self, compilation_ctx):
            expression = 2 % NodeModel.list_field  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "$p0 % v1"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rmod_with_nested_list_field(self, compilation_ctx):
            expression = 2 % any_(NodeModel.nested_list).field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "$p0 % v1.field"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionPow:
        def test_node_expression_pow_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field**2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.field ^ $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_pow_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field**2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "v0.nested.field ^ $p0"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_pow_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field**2  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "v1 ^ $p0"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_pow_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field ** 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "v1.field ^ $p0"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

    class TestNodeExpressionRpow:
        def test_node_expression_rpow_with_top_level_field(self, compilation_ctx):
            expression = 2**NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 ^ v0.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rpow_with_nested_field(self, compilation_ctx):
            expression = 2**NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path is None
            assert compiled.expression_template == "$p0 ^ v0.nested.field"
            assert compiled.outer_template == "{innermost_template}"
            assert compiled.expression_variable == "v0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rpow_with_list_field(self, compilation_ctx):
            expression = 2**NodeModel.list_field  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "list_field.$any"
            assert compiled.expression_template == "$p0 ^ v1"
            assert compiled.outer_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_node_expression_rpow_with_nested_list_field(self, compilation_ctx):
            expression = 2 ** any_(NodeModel.nested_list).field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)
            assert compiled.full_path == "nested_list.$any.field"
            assert compiled.expression_template == "$p0 ^ v1.field"
            assert compiled.outer_template == "any(v1 IN v0.nested_list WHERE {innermost_template})"
            assert compiled.expression_variable == "v1"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
