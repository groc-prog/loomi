from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field

from loomi.exceptions import ModelInitializationError, PropertyAccessorError


@dataclass(frozen=True)
class _PropertyAccessor:
    _full_path: str
    _annotation: Any

    def __getattribute__(self, name: str):
        if name.startswith("_") or name in ["all_", "any_"]:
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
                if not base_path.endswith(("all_", "any_")):
                    base_path = f"{base_path}.any_"

        # Since a dict might contain any key, we allow all properties
        if origin is dict or origin is Dict:
            value_type = args[1] if len(args) > 1 else Any
            return _PropertyAccessor(f"{base_path}.{name}", value_type)

        # For other Pydantic models, we can validate that the property path is valid
        if (
            isinstance(current_type, type)
            and issubclass(current_type, BaseModel)
            and name in current_type.model_fields
        ):
            return _PropertyAccessor(
                f"{base_path}.{name}",
                current_type.model_fields[name].annotation,
            )

        raise PropertyAccessorError(
            f"{name} is not a valid property name for path {self._full_path}"
        )

    def all_(self) -> "_PropertyAccessor":
        return _PropertyAccessor(f"{self._full_path}.all_", self._annotation)

    def any_(self) -> "_PropertyAccessor":
        return _PropertyAccessor(f"{self._full_path}.any_", self._annotation)


class _LoomiModelMetaclass(type(BaseModel)):
    def __getattribute__(cls, name):
        # To prevent any recursive __getattribute__ calls we need to skip this handler if any
        # of the following are accessed
        # Note that accessing model_fields also accesses __pydantic_fields__
        if name in ["model_fields", "__pydantic_fields__", "__pydantic_complete__"]:
            return super().__getattribute__(name)

        # If we do not wait for the model building to complete, we will run into recursion issues
        if cls.__pydantic_complete__:

            model_fields = cls.model_fields
            if name in model_fields:
                return _PropertyAccessor(name, model_fields[name].annotation)

        return super().__getattribute__(name)


class _LoomiBase(BaseModel, ABC, metaclass=_LoomiModelMetaclass):
    _dirty_fields: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)

    model_config = ConfigDict(validate_assignment=True)

    def __setattr__(self, name, value):
        if name in self._dirty_fields and value == self._dirty_fields[name]:
            self._dirty_fields.pop(name)
        else:
            self._dirty_fields[name] = getattr(self, name)

        return super().__setattr__(name, value)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        reserved_fields = ["all_", "any_"]

        for reserved in reserved_fields:
            if reserved in cls.model_fields:
                raise ModelInitializationError(
                    f"{reserved} is a reserved field. Rename or remove it"
                )

    @computed_field
    @property
    def id(self) -> Optional[int]:
        """
        ID of the database entity. Will be `None` as long as the model is `not hydrated`.

        Returns:
            Optional[int]: The ID or `None` if not hydrated.
        """
        return self._id

    @computed_field
    @property
    def element_id(self) -> Optional[str]:
        """
        Element ID of the database entity. Will be `None` as long as the model is `not hydrated`.
        For clients using `Memgraph`, this will be the same as `id`.

        Returns:
            Optional[int]: The ElementID or `None` if not hydrated.
        """
        return self._element_id
