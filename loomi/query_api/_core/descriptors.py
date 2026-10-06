import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Dict, List, Union, get_args, get_origin

from pydantic import BaseModel

import loomi.query_api.functions.arithmetic as arithmetic_functions
import loomi.query_api.functions.comparison as comparison_functions
from loomi._core.types import NumericValue, QueryModelType
from loomi._logger import logger
from loomi.constants import ServerType
from loomi.exceptions import ModelError
from loomi.query_api._core.protocols import CompilableDescriptor, CompiledDescriptor
from loomi.query_api._core.templates import EntityIdExpressionTemplate

if TYPE_CHECKING:
    from loomi.query_api._core.context import CompilationContext
else:
    CompilationContext = object


class ListPathOperator(StrEnum):
    """Operators for list paths."""

    ANY = "$any"
    ALL = "$all"
    NONE = "$none"
    SINGLE = "$single"


@dataclass(frozen=True)
class FieldDescriptor(CompilableDescriptor):
    """Descriptor class used for building query paths for a model."""

    _full_path: str
    _annotation: Any
    _model_type: QueryModelType

    def __eq__(self, value: Any):  # type: ignore[override]
        return comparison_functions.equals(self, value)

    def __ne__(self, value: Any):  # type: ignore[override]
        return comparison_functions.not_equals(self, value)

    def __gt__(self, value: NumericValue):
        return comparison_functions.greater_than(self, value)

    def __ge__(self, value: NumericValue):
        return comparison_functions.greater_than_or_equal(self, value)

    def __lt__(self, value: NumericValue):
        return comparison_functions.less_than(self, value)

    def __le__(self, value: NumericValue):
        return comparison_functions.less_than_or_equal(self, value)

    def __add__(self, value: NumericValue):
        return arithmetic_functions.add(self, value)

    def __radd__(self, value: NumericValue):
        return arithmetic_functions.reflected_add(self, value)

    def __sub__(self, value: NumericValue):
        return arithmetic_functions.subtract(self, value)

    def __rsub__(self, value: NumericValue):
        return arithmetic_functions.reflected_subtract(self, value)

    def __mul__(self, value: NumericValue):
        return arithmetic_functions.multiply(self, value)

    def __rmul__(self, value: NumericValue):
        return arithmetic_functions.reflected_multiply(self, value)

    def __truediv__(self, value: NumericValue):
        return arithmetic_functions.divide(self, value)

    def __rtruediv__(self, value: NumericValue):
        return arithmetic_functions.reflected_divide(self, value)

    def __mod__(self, value: NumericValue):
        return arithmetic_functions.modulo(self, value)

    def __rmod__(self, value: NumericValue):
        return arithmetic_functions.reflected_modulo(self, value)

    def __pow__(self, value: NumericValue):
        return arithmetic_functions.pow_(self, value)

    def __rpow__(self, value: NumericValue):
        return arithmetic_functions.reflected_pow(self, value)

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
            inner_type = next((a for a in args if not isinstance(a, type(None))), None)
            if inner_type is not None:
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
                        ListPathOperator.ANY.name,
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
            inner_type = next((a for a in args if not isinstance(a, type(None))), Any)
            return FieldDescriptor(f"{self._full_path}[{index}]", inner_type, self._model_type)

        if origin in (dict, Dict) and len(args) > 1:
            inner_type = args[1] if len(args) > 1 else Any
            return FieldDescriptor(f"{self._full_path}.{index}", inner_type, self._model_type)

        # In some cases the inner type can not be determined (e.g. Dict[str, Any])
        # In such cases, we just assume that a simple property access should be performed
        return FieldDescriptor(f"{self._full_path}.{index}", Any, self._model_type)

    def _compile_descriptor(self, ctx: CompilationContext) -> CompiledDescriptor:
        logger.debug(
            "Compiling descriptor for model %s with path %s",
            self._model_type,
            self._full_path,
        )

        list_operators = {op.value for op in ListPathOperator}  # Set for O(1) lookup
        model_variable = ctx.get_variable(self._model_type)

        # Split the path to be able to handle any list operators
        path_parts = re.split(r"(\$all|\$any|\$none|\$single)", self._full_path)
        parts = [p.strip(".") for p in path_parts if p.strip()]

        # If we don't have any list operators, we can return directly
        if not any(p in list_operators for p in parts):
            logger.debug("Descriptor does not contain any list paths, compiling final output")
            return CompiledDescriptor(
                full_template="{innermost_template}",
                variable_path=f"{{variable}}.{self._full_path}",
                variable=model_variable,
                full_path=self._full_path,
            )

        # Get the path parts and their index so we can use them to build the full
        # template in reverse order (from inner-most to outer-most)
        operators = [(index, part) for index, part in enumerate(parts) if part in list_operators]

        start_var_id = ctx.get_variable_count()
        ctx.force_increment_variable_counter(len(operators))

        # Build the inner-most template first, as this will be the template part which
        # the rest of the templates will wrap around
        inner_var_id = start_var_id + len(operators) - 1
        full_template = "{innermost_template}"

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

            full_template = (
                f"{operator_name}({iter_variable} IN {parent_variable}.{path_segment} "
                f"WHERE {full_template})"
            )

        # If there is any part of the path remaining after the last list operator, we have to append
        # it to the final target path
        variable_path = "{variable}"

        last_operator_index = operators[-1][0]
        if last_operator_index < (len(parts) - 1):
            cutoff_index = last_operator_index + 1
            remaining_paths = ".".join(parts[cutoff_index:])

            variable_path = f"{variable_path}.{remaining_paths}"

        return CompiledDescriptor(
            full_template=full_template,
            variable_path=variable_path,
            variable=f"v{inner_var_id}",
            full_path=self._full_path,
        )


@dataclass(frozen=True)
class EntityIdDescriptor(CompilableDescriptor):
    """Descriptor class used to apply entity ID functions."""

    _model_type: QueryModelType
    _template: EntityIdExpressionTemplate

    def _compile_descriptor(self, ctx: CompilationContext) -> CompiledDescriptor:
        logger.debug(
            "Compiling entity ID descriptor for model %s with template %s",
            self._model_type,
            self._template,
        )
        model_variable = ctx.get_variable(self._model_type)

        if ctx.server_type == ServerType.MEMGRAPH:
            logger.debug(
                "Server type defined as %s, which is not compatible with template %s. "
                "Falling back to %s",
                ctx.server_type.value,
                self._template.name,
                EntityIdExpressionTemplate.ID.name,
            )
            variable_path = EntityIdExpressionTemplate.ID.format(variable="{variable}")
        else:
            variable_path = self._template.format(variable="{variable}")

        return CompiledDescriptor(
            full_template="{innermost_template}",
            variable_path=variable_path,
            variable=model_variable,
            full_path=None,
        )
