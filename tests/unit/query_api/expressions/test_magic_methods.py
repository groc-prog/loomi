# pylint: disable=unused-import, redefined-outer-name, unused-argument, line-too-long, unused-variable, comparison-with-callable

from typing import Any, List

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import Expression
from loomi.query_api._core.protocols import CompiledExpression
from loomi.query_api.functions.collection import any_
from loomi.query_api.functions.comparison import equals


class NestedField(BaseModel):
    field: Any


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


class TestExpressionsMagicMethods:

    class TestExpressionEq:
        def test_expression_eq_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field = $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_expression_eq_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field = $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_expression_eq_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE v1 = $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_expression_eq_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field == "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE v1.field = $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

    class TestExpressionNe:
        def test_expression_ne_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field <> $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_expression_ne_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field <> $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_expression_ne_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE v1 <> $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

        def test_expression_ne_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field != "foo"
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE v1.field <> $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == "foo"

    class TestExpressionGt:
        def test_expression_gt_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field > 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field > $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_gt_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field > 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field > $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_gt_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field > 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE v1 > $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_gt_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field > 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE v1.field > $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestExpressionGte:
        def test_expression_gte_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field >= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field >= $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_gte_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field >= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field >= $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_gte_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field >= 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE v1 >= $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_gte_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field >= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE v1.field >= $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestExpressionLt:
        def test_expression_lt_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field < 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field < $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_lt_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field < 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field < $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_lt_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field < 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE v1 < $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_lt_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field < 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE v1.field < $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestExpressionLte:
        def test_expression_lte_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field <= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field <= $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_lte_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field <= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field <= $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_lte_with_list_field(self, compilation_ctx):
            expression = NodeModel.list_field <= 1  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE v1 <= $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_lte_with_nested_list_field(self, compilation_ctx):
            expression = any_(NodeModel.nested_list).field <= 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE v1.field <= $p0)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

    class TestExpressionAdd:
        def test_expression_add_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field + 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field + $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_add_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field + 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field + $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_add_with_list_field(self, compilation_ctx):
            expression = equals(NodeModel.list_field + 1, 2)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE (v1 + $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

        def test_expression_add_with_nested_list_field(self, compilation_ctx):
            expression = equals(any_(NodeModel.nested_list).field + 1, 2)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE (v1.field + $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

    class TestExpressionRadd:
        def test_expression_radd_with_top_level_field(self, compilation_ctx):
            expression = 1 + NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 + v0.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_radd_with_nested_field(self, compilation_ctx):
            expression = 1 + NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 + v0.nested.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_radd_with_list_field(self, compilation_ctx):
            expression = equals(1 + NodeModel.list_field, 2)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE ($p0 + v1) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

        def test_expression_radd_with_nested_list_field(self, compilation_ctx):
            expression = equals(1 + any_(NodeModel.nested_list).field, 2)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE ($p0 + v1.field) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

    class TestExpressionSub:
        def test_expression_sub_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field - 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field - $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_sub_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field - 1
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field - $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_sub_with_list_field(self, compilation_ctx):
            expression = equals(NodeModel.list_field - 1, 2)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE (v1 - $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

        def test_expression_sub_with_nested_list_field(self, compilation_ctx):
            expression = equals(any_(NodeModel.nested_list).field - 1, 2)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE (v1.field - $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

    class TestExpressionRsub:
        def test_expression_rsub_with_top_level_field(self, compilation_ctx):
            expression = 1 - NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 - v0.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_rsub_with_nested_field(self, compilation_ctx):
            expression = 1 - NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 - v0.nested.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1

        def test_expression_rsub_with_list_field(self, compilation_ctx):
            expression = equals(1 - NodeModel.list_field, 2)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE ($p0 - v1) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

        def test_expression_rsub_with_nested_list_field(self, compilation_ctx):
            expression = equals(1 - any_(NodeModel.nested_list).field, 2)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE ($p0 - v1.field) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 1
            assert parameters.get("p1") == 2

    class TestExpressionMul:
        def test_expression_mul_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field * 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field * $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_mul_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field * 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field * $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_mul_with_list_field(self, compilation_ctx):
            expression = equals(NodeModel.list_field * 2, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE (v1 * $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_mul_with_nested_list_field(self, compilation_ctx):
            expression = equals(any_(NodeModel.nested_list).field * 2, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE (v1.field * $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionRmul:
        def test_expression_rmul_with_top_level_field(self, compilation_ctx):
            expression = 2 * NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 * v0.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rmul_with_nested_field(self, compilation_ctx):
            expression = 2 * NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 * v0.nested.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rmul_with_list_field(self, compilation_ctx):
            expression = equals(2 * NodeModel.list_field, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE ($p0 * v1) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_rmul_with_nested_list_field(self, compilation_ctx):
            expression = equals(2 * any_(NodeModel.nested_list).field, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE ($p0 * v1.field) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionTruediv:
        def test_expression_truediv_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field / 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field / $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_truediv_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field / 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field / $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_truediv_with_list_field(self, compilation_ctx):
            expression = equals(NodeModel.list_field / 2, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE (v1 / $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_truediv_with_nested_list_field(self, compilation_ctx):
            expression = equals(any_(NodeModel.nested_list).field / 2, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE (v1.field / $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionRtruediv:
        def test_expression_rtruediv_with_top_level_field(self, compilation_ctx):
            expression = 2 / NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 / v0.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rtruediv_with_nested_field(self, compilation_ctx):
            expression = 2 / NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 / v0.nested.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rtruediv_with_list_field(self, compilation_ctx):
            expression = equals(2 / NodeModel.list_field, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE ($p0 / v1) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_rtruediv_with_nested_list_field(self, compilation_ctx):
            expression = equals(2 / any_(NodeModel.nested_list).field, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE ($p0 / v1.field) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionMod:
        def test_expression_mod_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field % 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field % $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_mod_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field % 2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field % $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_mod_with_list_field(self, compilation_ctx):
            expression = equals(NodeModel.list_field % 2, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE (v1 % $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_mod_with_nested_list_field(self, compilation_ctx):
            expression = equals(any_(NodeModel.nested_list).field % 2, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE (v1.field % $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionRmod:
        def test_expression_rmod_with_top_level_field(self, compilation_ctx):
            expression = 2 % NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 % v0.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rmod_with_nested_field(self, compilation_ctx):
            expression = 2 % NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 % v0.nested.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rmod_with_list_field(self, compilation_ctx):
            expression = equals(2 % NodeModel.list_field, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE ($p0 % v1) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_rmod_with_nested_list_field(self, compilation_ctx):
            expression = equals(2 % any_(NodeModel.nested_list).field, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE ($p0 % v1.field) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionPow:
        def test_expression_pow_with_top_level_field(self, compilation_ctx):
            expression = NodeModel.field**2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.field ^ $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_pow_with_nested_field(self, compilation_ctx):
            expression = NodeModel.nested.field**2
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "v0.nested.field ^ $p0"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_pow_with_list_field(self, compilation_ctx):
            expression = equals(NodeModel.list_field**2, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE (v1 ^ $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_pow_with_nested_list_field(self, compilation_ctx):
            expression = equals(any_(NodeModel.nested_list).field ** 2, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE (v1.field ^ $p0) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

    class TestExpressionRpow:
        def test_expression_rpow_with_top_level_field(self, compilation_ctx):
            expression = 2**NodeModel.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 ^ v0.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rpow_with_nested_field(self, compilation_ctx):
            expression = 2**NodeModel.nested.field
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "$p0 ^ v0.nested.field"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2

        def test_expression_rpow_with_list_field(self, compilation_ctx):
            expression = equals(2**NodeModel.list_field, 4)  # type: ignore
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.list_field WHERE ($p0 ^ v1) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4

        def test_expression_rpow_with_nested_list_field(self, compilation_ctx):
            expression = equals(2 ** any_(NodeModel.nested_list).field, 4)
            assert isinstance(expression, Expression)

            compiled = expression._compile_expression(compilation_ctx)
            assert isinstance(compiled, CompiledExpression)

            query = compiled.to_query_string()
            assert query == "any(v1 IN v0.nested_list WHERE ($p0 ^ v1.field) = $p1)"

            parameters = compilation_ctx.get_parameters()
            assert parameters.get("p0") == 2
            assert parameters.get("p1") == 4
