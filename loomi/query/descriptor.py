import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel

from loomi._internal._types import NumericValue, QueryModelType
from loomi._logger import logger
from loomi.constants import ServerType
from loomi.exceptions import ModelError
from loomi.query._context import ExpressionContext
from loomi.query._protocols import CompilableDescriptor, CompilationPlan
from loomi.query._templates import (
    DbFunctionTemplate,
    EntityIdExpressionTemplate,
    ListPathOperator,
    ListPathOperatorTemplate,
)
from loomi.query.functions import (
    equals,
    greater_than,
    greater_than_or_equal,
    less_than,
    less_than_or_equal,
    not_equals,
)


@dataclass(frozen=True)
class PropertyDescriptor(CompilableDescriptor):
    """Descriptor class used for building query paths for the a model."""

    _full_path: str
    _annotation: Any
    _model_type: QueryModelType

    def __eq__(self, value: Any):  # type: ignore[override]
        return equals(self, value)

    def __ne__(self, value: Any):  # type: ignore[override]
        return not_equals(self, value)

    def __gt__(self, value: NumericValue):
        return greater_than(self, value)

    def __ge__(self, value: NumericValue):
        return greater_than_or_equal(self, value)

    def __lt__(self, value: NumericValue):
        return less_than(self, value)

    def __le__(self, value: NumericValue):
        return less_than_or_equal(self, value)

    def __getattribute__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)

        logger.debug(
            "Getting property descriptor for property %s at path %s", name, self._full_path
        )
        current_type = self._annotation
        origin = get_origin(current_type)
        args = get_args(current_type)

        base_path = self._full_path
        # If we encounter a list we get the first valid item type we find
        if origin is list or origin is List or origin is Union:
            inner_type = next((a for a in args if a is not type(None)), None)
            if inner_type:
                current_type = inner_type
                origin = get_origin(current_type)
                args = get_args(current_type)

                # To be able to handle this correctly later on in the query builder, we
                # define a special $any property
                if not base_path.endswith(tuple(member.value for member in ListPathOperator)):
                    logger.debug(
                        "List property accessed without defining a list path operator, falling back to %s",
                        ListPathOperator.ANY.value,
                    )
                    base_path = f"{base_path}.{ListPathOperator.ANY.value}"

        # Since a dict might contain any key, we allow all properties
        if origin is dict or origin is Dict:
            # For dicts, the value is the second argument
            value_type = args[1] if len(args) > 1 else Any
            return PropertyDescriptor(f"{base_path}.{name}", value_type, self._model_type)

        # For other Pydantic models, we can validate that the property path is valid
        if (
            isinstance(current_type, type)
            and issubclass(current_type, BaseModel)
            and name in current_type.model_fields
        ):
            return PropertyDescriptor(
                f"{base_path}.{name}", current_type.model_fields[name].annotation, self._model_type
            )

        raise ModelError(f"{name} is not a valid property name for path {self._full_path}")

    def __getitem__(self, index: Union[int, str]):
        current_type = self._annotation
        origin = get_origin(current_type)
        args = get_args(current_type)

        inner_type = Any
        if origin in (list, List, Union):
            inner_type = next((a for a in args if a is not type(None)), Any)
        elif origin in (dict, Dict) and len(args) > 1:
            inner_type = args[1] if len(args) > 1 else Any

        return PropertyDescriptor(f"{self._full_path}[{index}]", inner_type, self._model_type)

    def _compilation_plan(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> CompilationPlan:
        logger.debug(
            "Generating compilation plan for property descriptor for model %s with path %s",
            self._model_type,
            self._full_path,
        )
        list_path_members = [member.value for member in ListPathOperator]

        # TODO: This currently generates 2 loops when filtering 2 list expressions which are
        # combined by any logical operator. Check if combining them into a single loop improves
        # performance
        # Current:
        # `ANY(v1 IN v0.tags WHERE v1.name = "t1") OR ANY(v1 IN v0.tags WHERE v1.name = "t2")`
        # To check:
        # `ANY(v1 IN v0.tags WHERE v1.name = "t1" OR v1.name = "t2")`
        variable = ctx.get_variable(self._model_type)
        parameter = ctx.add_parameter(value) if value else None

        parts = re.split(r"(\$all|\$any|\$none|\$single)", self._full_path)
        normalized_parts = [part.strip(".") for part in parts if part.strip()]

        # If we don't have any list operators, we can return the compilation plan directly
        if not any(part in normalized_parts for part in list_path_members):
            path_str = ".".join(normalized_parts)
            return (
                expression_template.format(variable="{path}", parameter="${parameter}"),
                f"{variable}.{path_str}",
                parameter,
            )

        # Each nested level needs it's own loop variables, which should also not clash
        # with any other variables defined
        logger.debug("Found list path operators in property descriptor path")
        operators = [(i, p) for i, p in enumerate(normalized_parts) if p in list_path_members]

        start_var_idx = ctx._variable_counter
        ctx.force_increment_variable_counter(len(operators))

        # Build the query from inside out, as the innermost part is the one using
        # the provided template
        inner_var_idx = start_var_idx + len(operators) - 1
        final_part = normalized_parts[-1]

        # If the final part is a list operator, we need to omit it and use the innermost
        # directly variable instead
        logger.debug("Compiling innermost expression")
        template_path: str
        if final_part in list_path_members:
            template_path = f"v{inner_var_idx}"
            template = expression_template.format(variable="{path}", parameter="${parameter}")
        else:
            template_path = f"v{inner_var_idx}"
            template = expression_template.format(variable="{path}", parameter="${parameter}")

        for op_count in range(len(operators) - 1, -1, -1):
            part_idx, operator_str = operators[op_count]
            operator = ListPathOperatorTemplate[operator_str]
            property_name = normalized_parts[part_idx - 1]

            iter_var = f"v{start_var_idx + op_count}"

            # The parent variable is always either the base variable (referencing a model)
            # or the variable from the previous iteration
            if op_count == 0:
                parent_var = variable
            else:
                parent_var = f"v{start_var_idx + op_count - 1}"

            template = f"{operator}({iter_var} IN {parent_var}.{property_name} WHERE {template})"

        return (template, template_path, parameter)

    def _compile(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> str:
        template, path, parameter = self._compilation_plan(ctx, expression_template, value)
        return template.format(path=path, parameter=parameter)


@dataclass(frozen=True)
class EntityIdDescriptor(CompilableDescriptor):
    """Descriptor class used for building queries for entity IDs."""

    _template: EntityIdExpressionTemplate
    _model_type: QueryModelType
    _server_type: ServerType

    def _compilation_plan(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> CompilationPlan:
        logger.debug(
            "Generating compilation plan for entity ID descriptor for model %s",
            self._model_type.__name__,
        )
        variable = ctx.get_variable(self._model_type)
        parameter = ctx.add_parameter(value) if value else None

        variable_template = self._get_entity_id_template().value.format(variable=variable)
        template = expression_template.format(variable="{path}", parameter="${parameter}")

        return (template, variable_template, parameter)

    def _compile(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> str:
        template, path, parameter = self._compilation_plan(ctx, expression_template, value)
        return template.format(path=path, parameter=parameter)

    def _get_entity_id_template(self) -> EntityIdExpressionTemplate:
        if self._server_type == ServerType.MEMGRAPH:
            logger.debug("Server type defined as %s, falling back to ID", self._server_type.value)
            return EntityIdExpressionTemplate.ID

        return self._template


@dataclass(frozen=True)
class DbFunctionDescriptor(CompilableDescriptor):
    """Descriptor class used to apply DB functions to variables when building queries."""

    _template: DbFunctionTemplate
    _descriptor: CompilableDescriptor

    def _compilation_plan(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> CompilationPlan:
        logger.debug("Generating compilation plan for db function descriptor")
        plan: CompilationPlan = self._descriptor._compilation_plan(ctx, expression_template, value)
        # For some reason, pylint can not correctly infer this
        template, path, parameter = plan  # pylint: disable=unpacking-non-sequence

        return (template, self._template.value.format(variable=path), parameter)

    def _compile(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> str:
        template, path, parameter = self._compilation_plan(ctx, expression_template, value)
        return template.format(path=path, parameter=parameter)
