from dataclasses import dataclass
from typing import Any, Dict, List, Union, get_args, get_origin

from pydantic import BaseModel

from loomi.exceptions import ModelError
from loomi.models._internal._types import _ModelType


@dataclass(frozen=True)
class _PropertyDescriptor:
    _full_path: str
    _annotation: Any
    _model_type: _ModelType

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
                # define a special any_ property
                if not base_path.endswith(tuple(self._reserved)):
                    base_path = f"{base_path}.any_"

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

    def __getitem__(self, index: Union[int, str]) -> "_PropertyDescriptor":
        """
        Allows indexing into lists or dictionaries.
        Usage: descriptor[0] -> path.0
        """
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

    def all_(self) -> "_PropertyDescriptor":
        """
        Define that the list predicate should use `ALL`.

        Returns:
            _PropertyAccessor: The modified property accessor.
        """
        return _PropertyDescriptor(f"{self._full_path}.all_", self._annotation, self._model_type)

    def any_(self) -> "_PropertyDescriptor":
        """
        Define that the list predicate should use `ANY`.

        Returns:
            _PropertyAccessor: The modified property accessor.
        """
        return _PropertyDescriptor(f"{self._full_path}.any_", self._annotation, self._model_type)
