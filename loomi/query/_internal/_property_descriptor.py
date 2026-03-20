import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel

from loomi.exceptions import ModelError
from loomi.query._internal._types import _QueryModelType
from loomi.query.helpers import (
    _NumericValue,
    equals,
    greater_than,
    greater_than_or_equal,
    less_than,
    less_than_or_equal,
    not_equals,
)

if TYPE_CHECKING:
    from loomi.query._internal._expression import _ExpressionContext
else:
    _ExpressionContext = object


@dataclass(frozen=True)
class _PropertyDescriptor:
    _full_path: str
    _annotation: Any
    _model_type: _QueryModelType

    _list_operators = ["$all", "$any"]
    _reserved = ["all_", "any_"]

    def __getattribute__(self, name: str):
        if name.startswith("_") or name in self._reserved:
            return super().__getattribute__(name)

        current_type = self._annotation
        origin = get_origin(current_type)
        args = get_args(current_type)

        base_path = self._full_path
        # If we encounter a list we need to get the first valid item type we find
        if origin is list or origin is List or origin is Union:
            inner_type = next((a for a in args if a is not type(None)), None)
            if inner_type:
                current_type = inner_type
                origin = get_origin(current_type)
                args = get_args(current_type)

                # To be able to handle this correctly later on in the query builder, we
                # define a special $any property
                if not base_path.endswith(tuple(self._list_operators)):
                    base_path = f"{base_path}.$any"

        # Since a dict might contain any key, we allow all properties
        if origin is dict or origin is Dict:
            value_type = args[1] if len(args) > 1 else Any
            return _PropertyDescriptor(f"{base_path}.{name}", value_type, self._model_type)

        # For other Pydantic models, we can validate that the property path is valid
        if (
            isinstance(current_type, type)
            and issubclass(current_type, BaseModel)
            and name in current_type.model_fields
        ):
            return _PropertyDescriptor(
                f"{base_path}.{name}", current_type.model_fields[name].annotation, self._model_type
            )

        raise ModelError(f"{name} is not a valid property name for path {self._full_path}")

    def __getitem__(self, index: Union[int, str]):
        current_type = self._annotation
        origin = get_origin(current_type)
        args = get_args(current_type)

        # Determine the inner type to pass to the next descriptor
        inner_type = Any
        if origin in (list, List, Union):
            # Find the first non-None type in the Union or List
            inner_type = next((a for a in args if a is not type(None)), Any)
        elif origin in (dict, Dict) and len(args) > 1:
            # For dicts, the value is the second argument: Dict[Key, Value]
            inner_type = args[1]

        return _PropertyDescriptor(f"{self._full_path}[{index}]", inner_type, self._model_type)

    def _compile_path(
        self, ctx: _ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> str:
        variable = ctx.get_variable(self._model_type)
        parameter = ctx.add_parameter(value) if value else None

        parts = re.split(r"(\$all|\$any)", self._full_path)
        normalized_parts = [part.strip(".") for part in parts if part.strip()]

        # If we don't have any list operators, we can return the compiled template directly
        if not any(part in normalized_parts for part in ["$all", "$any"]):
            path_str = ".".join(normalized_parts)
            return expression_template.format(
                variable=f"{variable}.{path_str}", parameter=parameter
            )

        # Each nested level needs it's own loop variables, which should also not clash
        # with any other variables defined
        operators = [(i, p) for i, p in enumerate(normalized_parts) if p in ("$all", "$any")]

        start_var_idx = ctx._variable_counter
        ctx._variable_counter += len(operators)

        # Build the query from inside out, as the innermost part is the one using
        # the provided template
        inner_var_idx = start_var_idx + len(operators) - 1
        final_part = normalized_parts[-1]
        result = expression_template.format(
            variable=f"v{inner_var_idx}.{final_part}", parameter=parameter
        )

        for op_count in range(len(operators) - 1, -1, -1):
            part_idx, operator_str = operators[op_count]
            operator = operator_str.lstrip("$").upper()
            property_name = normalized_parts[part_idx - 1]

            iter_var = f"v{start_var_idx + op_count}"

            # The parent variable is always either the base variable (referencing a model)
            # or the variable from the previous iteration
            if op_count == 0:
                parent_var = variable
            else:
                parent_var = f"v{start_var_idx + op_count - 1}"

            result = f"{operator}({iter_var} IN {parent_var}.{property_name} WHERE {result})"

        return result

    def all_(self) -> "_PropertyDescriptor":
        """
        Define that the list predicate should use `ALL`.

        Returns:
            _PropertyAccessor: The modified property accessor.
        """
        return _PropertyDescriptor(f"{self._full_path}.$all", self._annotation, self._model_type)

    def any_(self) -> "_PropertyDescriptor":
        """
        Define that the list predicate should use `ANY`.

        Returns:
            _PropertyAccessor: The modified property accessor.
        """
        return _PropertyDescriptor(f"{self._full_path}.$any", self._annotation, self._model_type)

    def __eq__(self, value: Any):  # type: ignore[override]
        return equals(self, value)

    def __ne__(self, value: Any):  # type: ignore[override]
        return not_equals(self, value)

    def __gt__(self, value: _NumericValue):
        return greater_than(self, value)

    def __ge__(self, value: _NumericValue):
        return greater_than_or_equal(self, value)

    def __lt__(self, value: _NumericValue):
        return less_than(self, value)

    def __le__(self, value: _NumericValue):
        return less_than_or_equal(self, value)
