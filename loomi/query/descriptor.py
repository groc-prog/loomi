import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel

from loomi._internal._types import NumericValue, QueryModelType
from loomi._logger import logger
from loomi.constants import ServerType
from loomi.exceptions import ModelError
from loomi.query._context import QueryCompilationContext
from loomi.query._protocols import CompilableDescriptor, CompiledDescriptor
from loomi.query._templates import EntityIdExpressionTemplate
from loomi.query.transformers import DbFunctionTransformer


class ListPathOperator(StrEnum):
    """Operators for list paths."""

    ANY = "$any"
    ALL = "$all"
    NONE = "$none"
    SINGLE = "$single"


@dataclass(frozen=True)
class FieldDescriptor(CompilableDescriptor):
    """Descriptor class used for building query paths for the a model."""

    _full_path: str
    _annotation: Any
    _model_type: QueryModelType

    def __eq__(self, value: Any):  # type: ignore[override]
        from loomi.query.functions.comparison import equals

        return equals(self, value)

    def __ne__(self, value: Any):  # type: ignore[override]
        from loomi.query.functions.comparison import not_equals

        return not_equals(self, value)

    def __gt__(self, value: NumericValue):
        from loomi.query.functions.comparison import greater_than

        return greater_than(self, value)

    def __ge__(self, value: NumericValue):
        from loomi.query.functions.comparison import greater_than_or_equal

        return greater_than_or_equal(self, value)

    def __lt__(self, value: NumericValue):
        from loomi.query.functions.comparison import less_than

        return less_than(self, value)

    def __le__(self, value: NumericValue):
        from loomi.query.functions.comparison import less_than_or_equal

        return less_than_or_equal(self, value)

    def __getattribute__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)

        logger.debug("Getting descriptor for field %s at path %s", name, self._full_path)
        base_path = self._full_path
        current_annotation = self._annotation
        origin = get_origin(current_annotation)
        args = get_args(current_annotation)

        # If we encounter a list we get the first valid item type we find
        if origin is list or origin is List or origin is Union:
            inner_type = next((a for a in args if a is not type(None)), None)
            if inner_type:
                current_annotation = inner_type
                origin = get_origin(current_annotation)
                args = get_args(current_annotation)

                # If no list path operator is defined, we fall back to ListPathOperator.ANY
                if not base_path.endswith(tuple(member.value for member in ListPathOperator)):
                    logger.debug(
                        (
                            "List field accessed without defining a list path operator, falling "
                            "back to %s"
                        ),
                        ListPathOperator.ANY.value,
                    )
                    base_path = f"{base_path}.{ListPathOperator.ANY.value}"

        # Since a dict might contain any key, we allow all fields
        if origin is dict or origin is Dict:
            value_type = args[1] if len(args) > 1 else Any
            return FieldDescriptor(f"{base_path}.{name}", value_type, self._model_type)

        # For other Pydantic models, we can validate that the field path is valid
        if (
            isinstance(current_annotation, type)
            and issubclass(current_annotation, BaseModel)
            and name in current_annotation.model_fields
        ):
            return FieldDescriptor(
                f"{base_path}.{name}",
                current_annotation.model_fields[name].annotation,
                self._model_type,
            )

        raise ModelError(f"{name} is not a valid field name for path {self._full_path}")

    def __getitem__(self, index: Union[int, str]):
        current_type = self._annotation
        origin = get_origin(current_type)
        args = get_args(current_type)

        inner_type = Any
        if origin in (list, List, Union):
            inner_type = next((a for a in args if a is not type(None)), Any)
        elif origin in (dict, Dict) and len(args) > 1:
            inner_type = args[1] if len(args) > 1 else Any

        return FieldDescriptor(f"{self._full_path}[{index}]", inner_type, self._model_type)

    def _compile(
        self, ctx: QueryCompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledDescriptor:
        # TODO: This currently generates 2 loops when filtering 2 list expressions which are
        # combined by any logical operator. Check if combining them into a single loop improves
        # performance
        # Current:
        # `ANY(v1 IN v0.tags WHERE v1.name = "t1") OR ANY(v1 IN v0.tags WHERE v1.name = "t2")`
        # To check:
        # `ANY(v1 IN v0.tags WHERE v1.name = "t1" OR v1.name = "t2")`
        logger.debug(
            "Generating compilation template for descriptor for model %s with path %s",
            self._model_type,
            self._full_path,
        )

        list_operators = {op.value for op in ListPathOperator}  # Set for O(1) lookup
        model_variable = ctx.get_variable(self._model_type)

        if isinstance(value, DbFunctionTransformer):
            parameter_name = value._compile(ctx)
        else:
            parameter_name = f"${ctx.add_parameter(value)}" if value else None

        # Split the path to be able to handle any list operators
        path_parts = re.split(r"(\$all|\$any|\$none|\$single)", self._full_path)
        parts = [p.strip(".") for p in path_parts if p.strip()]

        # If we don't have any list operators, we can return directly
        if not any(p in list_operators for p in parts):
            logger.debug("Descriptor does not contain any list paths, compiling final output")
            template = expression_template.format(variable="{path}", parameter="{parameter}")
            return CompiledDescriptor(
                template, f"{model_variable}.{'.'.join(parts)}", parameter_name
            )

        # Get the path parts and their index so we can use them to build the full
        # template in reverse order (from inner-most to outer-most)
        operators = [(index, part) for index, part in enumerate(parts) if part in list_operators]

        start_var_id = ctx._variable_counter
        ctx.force_increment_variable_counter(len(operators))

        # Build the inner-most expression first, as this will be the template part which
        # the rest of the expression will wrap around
        inner_var_id = start_var_id + len(operators) - 1
        current_template = expression_template.format(variable="{path}", parameter="{parameter}")

        # The inner-most variable needs to be returned so it can be used by other expressions
        target_path = f"v{inner_var_id}"

        # Iterate through the remaining paths to build in reverse order, so the rest of the
        # expression is also build from the inside-out
        logger.debug("Compiling %d nested list operators", len(operators))
        for operators_index, (index, operator) in reversed(list(enumerate(operators))):
            iter_variable = f"v{start_var_id + operators_index}"
            parent_variable = (
                f"v{start_var_id + operators_index - 1}" if operators_index > 0 else model_variable
            )

            # Path is the part immediately preceding the operator
            path_segment = parts[index - 1]
            operator_name = operator.lstrip("$")

            current_template = (
                f"{operator_name}({iter_variable} IN {parent_variable}.{path_segment} "
                f"WHERE {current_template})"
            )

        return CompiledDescriptor(current_template, target_path, parameter_name)


@dataclass(frozen=True)
class EntityIdDescriptor(CompilableDescriptor):
    """Descriptor class used to apply entity ID functions."""

    model_type: QueryModelType
    template: EntityIdExpressionTemplate

    def _compile(
        self, ctx: QueryCompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledDescriptor:
        logger.debug(
            "Generating compilation plan for entity ID descriptor for model %s",
            self.model_type,
        )
        model_variable = ctx.get_variable(self.model_type)

        if ctx.server_type == ServerType.MEMGRAPH:
            logger.debug(
                "Server type defined as %s, falling back to %s",
                ctx.server_type.value,
                EntityIdExpressionTemplate.ID.name,
            )
            entity_id_path = EntityIdExpressionTemplate.ID.format(variable=model_variable)
        else:
            entity_id_path = self.template.format(variable=model_variable)

        if isinstance(value, DbFunctionTransformer):
            parameter_name = value._compile(ctx)
        else:
            parameter_name = ctx.add_parameter(value) if value else None

        template = expression_template.format(variable="{path}", parameter="${parameter}")
        return CompiledDescriptor(template, entity_id_path, parameter_name)
