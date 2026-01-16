# pylint: disable=arguments-differ

import pickle
from abc import ABC
from typing import Any, Dict, Optional

import xxhash
from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field


class _LoomiBase(BaseModel, ABC):
    _checksums: Dict[str, Optional[str]] = PrivateAttr(default_factory=dict)

    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    @computed_field
    @property
    def id(self) -> Optional[int]:
        """
        ID of the database entity. Will be `None` as long as the model is `not hydrated or
        persisted`.

        Returns:
            Optional[int]: The ID or `None` if not hydrated or persisted.
        """
        return self._id

    @computed_field
    @property
    def element_id(self) -> Optional[str]:
        """
        Element ID of the database entity. Will be `None` as long as the model is `not hydrated
        or persisted`. For clients using `Memgraph`, this will be the same as `id`.

        Returns:
            Optional[int]: The ElementID or `None` if not hydrated or persisted.
        """
        return self._element_id

    def model_post_init(self, context: Any) -> None:
        self._checksums = self._compute_checksums()

    def _compute_checksums(self) -> Dict[str, Optional[str]]:
        checksums: Dict[str, Optional[str]] = {}

        for field_name in self.__class__.model_fields.keys():
            value = getattr(self, field_name)
            if value is None:
                checksums[field_name] = None
            else:
                dump = pickle.dumps(value)
                checksums[field_name] = xxhash.xxh64(dump).hexdigest()

        return checksums
