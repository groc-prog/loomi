from abc import ABC
from typing import Any, Dict, Optional, TypedDict

from neo4j.graph import Graph
from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field


class LoomiBaseConfiguration(TypedDict, total=False):
    """TypedDict for configuring Loomi model/client behavior."""

    skip_constraints: bool
    """Skips creating defined constraints when initializing model."""

    skip_indexes: bool
    """Skips creating defined indexes when initializing model."""

    serialize_nested: bool
    """
    Serializes nested objects when storing fields (Neo4j only). If set to `False`,
    attempting to store a nested objects will result in a exception.
    """


class _LoomiBase(BaseModel, ABC):
    _dirty_fields: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _id: Optional[int] = PrivateAttr(default=None)
    _element_id: Optional[str] = PrivateAttr(default=None)
    _graph: Optional[Graph] = PrivateAttr(default=None)

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
