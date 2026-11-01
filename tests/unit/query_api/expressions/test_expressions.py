# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

import re
from typing import Any, List

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import CompoundExpression, Expression, InvertExpression
from loomi.query_api._core.protocols import CompiledExpression
from loomi.query_api.functions.arithmetic import add, divide, multiply
from loomi.query_api.functions.collection import any_, single
from loomi.query_api.functions.comparison import and_, equals, not_, or_
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


class TestExpression:
    def test_expression_with_static_value_as_right_side(self, compilation_ctx):
        expression = equals(NodeModel.field, 2)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.field = $p0"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2

    def test_expression_with_static_value_as_left_side(self, compilation_ctx):
        expression = equals(2, NodeModel.field)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "$p0 = v0.field"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2

    def test_expression_with_field_path_on_both_sides(self, compilation_ctx):
        expression = equals(NodeModel.field, NodeModel.field)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.field = v0.field"

        parameters = compilation_ctx.get_parameters()
        assert len(parameters) == 0

    def test_expression_raises_if_right_side_is_list_path(self, compilation_ctx):
        expression = NodeModel.field == NodeModel.list_field
        assert isinstance(expression, Expression)

        with pytest.raises(
            QueryError,
            match=re.escape(
                "Invalid right side of expression passed. Expected primitive value, DB function, nested expression or field descriptor without list path operators, but got list_field.$any"
            ),
        ):
            expression._compile_expression(compilation_ctx)

    def test_expression_with_nested_expression_as_right_side(self, compilation_ctx):
        expression = equals(NodeModel.field, add(NodeModel.field, 2))
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.field = (v0.field + $p0)"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2

    def test_expression_with_nested_expression_as_left_side(self, compilation_ctx):
        expression = equals(add(NodeModel.field, 2), NodeModel.field)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "(v0.field + $p0) = v0.field"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2

    def test_expression_with_deeply_nested_expression(self, compilation_ctx):
        expression = equals(divide(multiply(add(NodeModel.field, 2), 5), 10), 13)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "(((v0.field + $p0) * $p1) / $p2) = $p3"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 5
        assert parameters.get("p2") == 10
        assert parameters.get("p3") == 13

    def test_expression_raises_if_nested_expression_contains_list_path(self, compilation_ctx):
        expression = equals(NodeModel.field, add(NodeModel.list_field, 2))
        assert isinstance(expression, Expression)

        with pytest.raises(
            QueryError,
            match=re.escape(
                "Invalid right side of expression passed. Expected primitive value, DB function, nested expression or field descriptor without list path operators, but got list_field.$any"
            ),
        ):
            expression._compile_expression(compilation_ctx)

    def test_expression_with_db_function_wrapping_descriptor_on_right_side(self, compilation_ctx):
        expression = equals(NodeModel.field, to_lower(NodeModel.field))
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.field = toLower(v0.field)"

        parameters = compilation_ctx.get_parameters()
        assert len(parameters) == 0

    def test_expression_with_db_function_wrapping_descriptor_on_left_side(self, compilation_ctx):
        expression = equals(to_lower(NodeModel.field), NodeModel.field)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "toLower(v0.field) = v0.field"

        parameters = compilation_ctx.get_parameters()
        assert len(parameters) == 0

    def test_expression_with_db_function_wrapping_value_on_right_side(self, compilation_ctx):
        expression = equals(NodeModel.field, to_lower("fOo"))
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "v0.field = toLower($p0)"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == "fOo"

    def test_expression_with_db_function_wrapping_value_on_left_side(self, compilation_ctx):
        expression = equals(to_lower("fOo"), NodeModel.field)
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "toLower($p0) = v0.field"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == "fOo"

    def test_expression_with_deeply_nested_db_function(self, compilation_ctx):
        expression = equals(to_upper(ltrim(rtrim(NodeModel.field))), "FOO")
        assert isinstance(expression, Expression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "toUpper(ltrim(rtrim(v0.field))) = $p0"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == "FOO"


class TestInvertExpression:
    def test_invert_expression_with_expression(self, compilation_ctx):
        expression = not_(equals(NodeModel.field, 2))
        assert isinstance(expression, InvertExpression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "NOT(v0.field = $p0)"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2

    def test_invert_expression_with_compound_expression(self, compilation_ctx):
        expression = not_(or_(equals(NodeModel.field, 2), equals(NodeModel.field, 5)))
        assert isinstance(expression, InvertExpression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "NOT(v0.field = $p0 OR v0.field = $p1)"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 5

    def test_invert_expression_with_compound_expression_with_magic_method(self, compilation_ctx):
        expression = ~(or_(equals(NodeModel.field, 2), equals(NodeModel.field, 5)))
        assert isinstance(expression, InvertExpression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "NOT(v0.field = $p0 OR v0.field = $p1)"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 5

    def test_invert_expression_with_magic_method(self, compilation_ctx):
        expression = ~(NodeModel.field + 2)
        assert isinstance(expression, InvertExpression)

        compiled = expression._compile_expression(compilation_ctx)
        assert isinstance(compiled, CompiledExpression)

        query = compiled.to_query_string()
        assert query == "NOT(v0.field + $p0)"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2


class TestCompoundExpression:
    def test_compound_expression_and_with_magic_method(self, compilation_ctx):
        expression = (NodeModel.field == 2) & (NodeModel.field == 4)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "v0.field = $p0 AND v0.field = $p1"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4

    def test_compound_expression_and_with_magic_method_with_other_compound_expression_with_same_operator(
        self, compilation_ctx
    ):
        compound_expression = (NodeModel.field == 2) & (NodeModel.field == 4)
        expression = compound_expression & (NodeModel.field == 6)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "v0.field = $p0 AND v0.field = $p1 AND v0.field = $p2"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4
        assert parameters.get("p2") == 6

    def test_compound_expression_and_with_magic_method_with_other_compound_expression_with_other_operator(
        self, compilation_ctx
    ):
        compound_expression = (NodeModel.field == 2) | (NodeModel.field == 4)
        expression = compound_expression & (NodeModel.field == 6)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "(v0.field = $p0 OR v0.field = $p1) AND v0.field = $p2"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4
        assert parameters.get("p2") == 6

    def test_compound_expression_or_with_magic_method(self, compilation_ctx):
        expression = (NodeModel.field == 2) | (NodeModel.field == 4)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "v0.field = $p0 OR v0.field = $p1"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4

    def test_compound_expression_or_with_magic_method_with_other_compound_expression_with_same_operator(
        self, compilation_ctx
    ):
        compound_expression = (NodeModel.field == 2) | (NodeModel.field == 4)
        expression = compound_expression | (NodeModel.field == 6)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "v0.field = $p0 OR v0.field = $p1 OR v0.field = $p2"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4
        assert parameters.get("p2") == 6

    def test_compound_expression_or_with_magic_method_with_other_compound_expression_with_other_operator(
        self, compilation_ctx
    ):
        compound_expression = (NodeModel.field == 2) & (NodeModel.field == 4)
        expression = compound_expression | (NodeModel.field == 6)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "(v0.field = $p0 AND v0.field = $p1) OR v0.field = $p2"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4
        assert parameters.get("p2") == 6

    def test_compound_expression_xor_with_magic_method(self, compilation_ctx):
        expression = (NodeModel.field == 2) ^ (NodeModel.field == 4)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "v0.field = $p0 XOR v0.field = $p1"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4

    def test_compound_expression_xor_with_magic_method_with_other_compound_expression_with_same_operator(
        self, compilation_ctx
    ):
        compound_expression = (NodeModel.field == 2) ^ (NodeModel.field == 4)
        expression = compound_expression ^ (NodeModel.field == 6)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "v0.field = $p0 XOR v0.field = $p1 XOR v0.field = $p2"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4
        assert parameters.get("p2") == 6

    def test_compound_expression_xor_with_magic_method_with_other_compound_expression_with_other_operator(
        self, compilation_ctx
    ):
        compound_expression = (NodeModel.field == 2) & (NodeModel.field == 4)
        expression = compound_expression ^ (NodeModel.field == 6)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert query == "(v0.field = $p0 AND v0.field = $p1) XOR v0.field = $p2"

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 4
        assert parameters.get("p2") == 6

    def test_compound_expression_optimizes_list_paths(self, compilation_ctx):
        expression = (any_(NodeModel.nested_list).field == 2) | (
            any_(NodeModel.nested_list).other_field == 3
        )
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        pattern = (
            r"any\((v\d+) IN v0\.nested_list WHERE \1\.field = \$p0 OR \1\.other_field = \$p1\)"
        )

        assert re.fullmatch(pattern, query) is not None

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 3

    def test_compound_expression_does_not_optimize_list_paths_with_different_operators(
        self, compilation_ctx
    ):
        expression = (any_(NodeModel.nested_list).field == 2) | (
            single(NodeModel.nested_list).field == 3
        )
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)

        assert (
            query
            == "any(v1 IN v0.nested_list WHERE v1.field = $p0) OR single(v2 IN v0.nested_list WHERE v2.field = $p1)"
        )

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 3

    def test_compound_expression_does_not_optimize_different_list_paths(self, compilation_ctx):
        expression = (any_(NodeModel.nested_list).field == 2) | (NodeModel.list_field == 3)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert (
            query
            == "any(v1 IN v0.nested_list WHERE v1.field = $p0) OR any(v2 IN v0.list_field WHERE v2 = $p1)"
        )

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 3

    def test_compound_expression_does_not_optimize_different_list_paths_from_other_compound_expressions(
        self, compilation_ctx
    ):
        expression1 = (any_(NodeModel.nested_list).field == 2) | (NodeModel.list_field == 3)
        expression2 = (any_(NodeModel.nested_list).field == 4) & (NodeModel.list_field == 5)

        expression = and_(expression1, expression2)
        assert isinstance(expression, CompoundExpression)

        query = expression.to_query_string(compilation_ctx)
        assert (
            query
            == "(any(v1 IN v0.nested_list WHERE v1.field = $p0) OR any(v2 IN v0.list_field WHERE v2 = $p1)) AND any(v3 IN v0.nested_list WHERE v3.field = $p2) AND any(v4 IN v0.list_field WHERE v4 = $p3)"
        )

        parameters = compilation_ctx.get_parameters()
        assert parameters.get("p0") == 2
        assert parameters.get("p1") == 3
        assert parameters.get("p2") == 4
        assert parameters.get("p3") == 5
