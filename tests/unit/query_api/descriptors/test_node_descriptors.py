# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

import re
from typing import Any, Dict, List

import pytest
from pydantic import BaseModel

from loomi.constants import ServerType
from loomi.exceptions import ModelError
from loomi.graph.node import Node
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.descriptors import EntityIdDescriptor, FieldDescriptor
from loomi.query_api._core.protocols import CompiledDescriptor
from loomi.query_api.functions.collection import all_, any_, none, single
from loomi.query_api.functions.identity import element_id, id_


class DeeplyNestedField(BaseModel):
    deeply_nested_field: str


class NestedField(BaseModel):
    dict_field: Dict[str, Any]
    deeply_nested: DeeplyNestedField


class NestedListField(BaseModel):
    deeply_nested: List[DeeplyNestedField]


class NodeModel(Node):
    top_level_field: str
    dict_field: Dict[str, Any]
    nested: NestedField
    list_field: List[str]
    nested_list: List[NestedListField]


@pytest.fixture
def compilation_ctx(server_type):
    ctx = CompilationContext(server_type)
    ctx.add_model(NodeModel)

    return ctx


def assert_path_matches(pattern: str, path: str) -> None:
    assert re.match(pattern, path) is not None, f"{path} should match pattern {pattern}"


@pytest.mark.parametrize("server_type", [ServerType.NEO4J, ServerType.MEMGRAPH])
class TestNodeDescriptor:
    def test_node_descriptor_raises_if_field_does_not_exist(self, compilation_ctx):
        with pytest.raises(
            ModelError, match="bar is not a valid field name for path top_level_field"
        ):
            _ = NodeModel.top_level_field.bar  # type: ignore

    def test_node_descriptor_on_top_level_fields(self, compilation_ctx):
        descriptor = NodeModel.top_level_field
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "{variable}.top_level_field"
        assert compiled.variable == "v0"

    def test_node_descriptor_on_nested_field(self, compilation_ctx):
        descriptor = NodeModel.nested.deeply_nested.deeply_nested_field
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "{variable}.nested.deeply_nested.deeply_nested_field"
        assert compiled.variable == "v0"

    def test_node_descriptor_on_dict_field(self, compilation_ctx):
        descriptor = NodeModel.dict_field["keya"]["keyb"]
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "{variable}.dict_field.keya.keyb"
        assert compiled.variable == "v0"

    def test_node_descriptor_on_nested_dict_field(self, compilation_ctx):
        descriptor = NodeModel.nested.dict_field["keya"]["keyb"]
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "{variable}.nested.dict_field.keya.keyb"
        assert compiled.variable == "v0"

    def test_node_descriptor_on_list_field_with_index(self, compilation_ctx):
        descriptor = NodeModel.list_field[2]
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "{variable}.list_field[2]"
        assert compiled.variable == "v0"

    def test_node_descriptor_on_list_field_uses_any_by_default(self, compilation_ctx):
        descriptor = NodeModel.list_field
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "list_field.$any"
        assert compiled.full_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v1"

    def test_node_descriptor_on_list_field_with_all_operator(self, compilation_ctx):
        descriptor = all_(NodeModel.list_field)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "list_field.$all"
        assert compiled.full_template == "all(v1 IN v0.list_field WHERE {innermost_template})"
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v1"

    def test_node_descriptor_on_list_field_with_any_operator(self, compilation_ctx):
        descriptor = any_(NodeModel.list_field)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "list_field.$any"
        assert compiled.full_template == "any(v1 IN v0.list_field WHERE {innermost_template})"
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v1"

    def test_node_descriptor_on_list_field_with_none_operator(self, compilation_ctx):
        descriptor = none(NodeModel.list_field)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "list_field.$none"
        assert compiled.full_template == "none(v1 IN v0.list_field WHERE {innermost_template})"
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v1"

    def test_node_descriptor_on_list_field_with_single_operator(self, compilation_ctx):
        descriptor = single(NodeModel.list_field)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "list_field.$single"
        assert compiled.full_template == "single(v1 IN v0.list_field WHERE {innermost_template})"
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v1"

    def test_node_descriptor_on_nested_list_field_with_index(self, compilation_ctx):
        descriptor = NodeModel.nested_list[2].deeply_nested[5]
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "{variable}.nested_list[2].deeply_nested[5]"
        assert compiled.variable == "v0"

    def test_node_descriptor_on_nested_list_field_with_all_operator(self, compilation_ctx):
        descriptor = all_(all_(NodeModel.nested_list).deeply_nested)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "nested_list.$all.deeply_nested.$all"
        assert (
            compiled.full_template
            == "all(v1 IN v0.nested_list WHERE all(v2 IN v1.deeply_nested WHERE {innermost_template}))"
        )
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v2"

    def test_node_descriptor_on_nested_list_field_with_any_operator(self, compilation_ctx):
        descriptor = any_(any_(NodeModel.nested_list).deeply_nested)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "nested_list.$any.deeply_nested.$any"
        assert (
            compiled.full_template
            == "any(v1 IN v0.nested_list WHERE any(v2 IN v1.deeply_nested WHERE {innermost_template}))"
        )
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v2"

    def test_node_descriptor_on_nested_list_field_with_none_operator(self, compilation_ctx):
        descriptor = none(none(NodeModel.nested_list).deeply_nested)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "nested_list.$none.deeply_nested.$none"
        assert (
            compiled.full_template
            == "none(v1 IN v0.nested_list WHERE none(v2 IN v1.deeply_nested WHERE {innermost_template}))"
        )
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v2"

    def test_node_descriptor_on_nested_list_field_with_single_operator(self, compilation_ctx):
        descriptor = single(single(NodeModel.nested_list).deeply_nested)
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "nested_list.$single.deeply_nested.$single"
        assert (
            compiled.full_template
            == "single(v1 IN v0.nested_list WHERE single(v2 IN v1.deeply_nested WHERE {innermost_template}))"
        )
        assert compiled.variable_path == "{variable}"
        assert compiled.variable == "v2"

    def test_node_descriptor_on_nested_list_field_with_inner_variable_path(self, compilation_ctx):
        descriptor = all_(any_(NodeModel.nested_list).deeply_nested).deeply_nested_field
        assert isinstance(descriptor, FieldDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path == "nested_list.$any.deeply_nested.$all.deeply_nested_field"
        assert (
            compiled.full_template
            == "any(v1 IN v0.nested_list WHERE all(v2 IN v1.deeply_nested WHERE {innermost_template}))"
        )
        assert compiled.variable_path == "{variable}.deeply_nested_field"
        assert compiled.variable == "v2"


@pytest.mark.parametrize("server_type", [ServerType.NEO4J, ServerType.MEMGRAPH])
class TestNodeEntityIdDescriptor:
    def test_node_entity_descriptor_with_id(self, compilation_ctx):
        descriptor = id_(NodeModel)
        assert isinstance(descriptor, EntityIdDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable_path == "id({variable})"
        assert compiled.variable == "v0"

    def test_node_entity_descriptor_with_element_id(self, compilation_ctx, server_type):
        descriptor = element_id(NodeModel)
        assert isinstance(descriptor, EntityIdDescriptor)

        compiled = descriptor._compile_descriptor(compilation_ctx)
        assert isinstance(compiled, CompiledDescriptor)
        assert compiled.full_path is None
        assert compiled.full_template == "{innermost_template}"
        assert compiled.variable == "v0"

        if server_type == ServerType.NEO4J:
            assert compiled.variable_path == "elementId({variable})"
        else:
            assert compiled.variable_path == "id({variable})"
