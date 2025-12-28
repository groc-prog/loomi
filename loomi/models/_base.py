from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field


@dataclass(frozen=True)
class _QueryAccessor:
    name: str
    annotation: Any


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
                return _QueryAccessor(name, model_fields[name].annotation)

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
