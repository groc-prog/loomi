from abc import ABC
from typing import Optional

from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field


class _LoomiBase(BaseModel, ABC):
    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

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
