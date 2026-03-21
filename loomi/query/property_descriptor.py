import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel

from loomi._internal._types import _NumericValue, _QueryModelType
from loomi._logger import _logger
from loomi.exceptions import ModelError, QueryError
from loomi.query.helpers import (
    AliasedModel,
    equals,
    greater_than,
    greater_than_or_equal,
    less_than,
    less_than_or_equal,
    not_equals,
)

if TYPE_CHECKING:
    from loomi.query.expressions import _ExpressionContext
else:
    _ExpressionContext = object


class _ListOperator(StrEnum):
    ANY = "$any"
    ALL = "$all"


@dataclass(frozen=True)
class PropertyDescriptor:
    """Descriptor class used for building query paths for the a model."""

    _full_path: str
    _annotation: Any
    _model_type: _QueryModelType

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
                if not base_path.endswith(tuple(member.value for member in _ListOperator)):
                    base_path = f"{base_path}.{_ListOperator.ANY.value}"

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

        # Determine the inner type to pass to the next descriptor
        inner_type = Any
        if origin in (list, List, Union):
            inner_type = next((a for a in args if a is not type(None)), Any)
        elif origin in (dict, Dict) and len(args) > 1:
            # For dicts, the value is the second argument
            inner_type = args[1] if len(args) > 1 else Any

        return PropertyDescriptor(f"{self._full_path}[{index}]", inner_type, self._model_type)

    def _compile_path(
        self, ctx: _ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> str:
        _logger.debug(
            "Compiling path %s for %s",
            self._full_path,
            (
                f"alias {self._model_type._alias}"
                if isinstance(self._model_type, AliasedModel)
                else self._model_type.__name__
            ),
        )
        # TODO: This currently generates 2 loops when filtering 2 list expressions which are
        # combined by any logical operator. Check if combining them into a single loop improves
        # performance
        # Current:
        # `ANY(v1 IN v0.tags WHERE v1.name = "t1") OR ANY(v1 IN v0.tags WHERE v1.name = "t2")`
        # To check:
        # `ANY(v1 IN v0.tags WHERE v1.name = "t1" OR v1.name = "t2")`
        variable = ctx.get_variable(self._model_type)
        parameter = ctx.add_parameter(value) if value else None

        parts = re.split(r"(\$all|\$any)", self._full_path)
        normalized_parts = [part.strip(".") for part in parts if part.strip()]

        # If we don't have any list operators, we can return the compiled template directly
        if not any(part in normalized_parts for part in [member.value for member in _ListOperator]):
            path_str = ".".join(normalized_parts)
            return expression_template.format(
                variable=f"{variable}.{path_str}", parameter=parameter
            )

        # Each nested level needs it's own loop variables, which should also not clash
        # with any other variables defined
        operators = [
            (i, p)
            for i, p in enumerate(normalized_parts)
            if p in (member.value for member in _ListOperator)
        ]

        start_var_idx = ctx.__variable_counter
        ctx.force_increment_variable_counter(len(operators))

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

    def compiled_path(self) -> str:
        """
        Compiles the path into a string in the format `nested.property`. The compiled path does
        not include a variable for the model itself.

        [!NOTE] This function only supports list paths which use a index. Paths using `any_()`
        or `all_()` are not supported and will raise a exception.

        Raises:
            QueryError: If the path contains `any_()` or `all_()`.

        Returns:
            str: The compiled path.
        """
        if any(member.value in self._full_path for member in _ListOperator):
            raise QueryError(
                "Compiled paths with `any_()` or `all_()` are not supported. If "
                "you want to use the compiled path with the `cypher()` helper while trying to use "
                "the `ALL` or `ANY` Cypher functions, you should write the path yourself."
            )

        return self._full_path

    def all_(self) -> "PropertyDescriptor":
        """
        Define that the list predicate should use `ALL`.

        Returns:
            _PropertyAccessor: The modified property accessor.
        """
        return PropertyDescriptor(f"{self._full_path}.$all", self._annotation, self._model_type)

    def any_(self) -> "PropertyDescriptor":
        """
        Define that the list predicate should use `ANY`.

        Returns:
            _PropertyAccessor: The modified property accessor.
        """
        return PropertyDescriptor(f"{self._full_path}.$any", self._annotation, self._model_type)

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
