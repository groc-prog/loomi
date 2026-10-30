# pylint: disable=missing-class-docstring

import hashlib
from typing import Any, ClassVar, Dict, Optional, Self, cast

from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field

from loomi._core.types import ModelType
from loomi.logger import get_logger
from loomi.query_api._core.descriptors import FieldDescriptor

logger = get_logger("model")


class ModelMixinMetaclass(type(BaseModel)):
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
                return FieldDescriptor(name, model_fields[name].annotation, cast(ModelType, cls))

        return super().__getattribute__(name)


class ModelMixin(BaseModel, metaclass=ModelMixinMetaclass):
    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)
    _alias_cache: ClassVar[Dict[str, str]] = {}

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        # Build alias cache once so we do not have to look it up during de-serialization each time
        for field_name, field_info in cls.model_fields.items():
            if field_info.alias is not None:
                cls._alias_cache[field_info.alias] = field_name

    def __eq__(self, value: Any) -> bool:
        if type(self) is not type(value):
            return False

        if self._element_id is None and value._element_id is None:
            return super().__eq__(value)

        return self._element_id == value._element_id

    @computed_field
    @property
    def id(self) -> Optional[int]:
        """
        ID of the database entity. Will be `None` as long as the model is **not hydrated or
        persisted**.

        Returns:
            Optional[int]: The ID or `None` if not hydrated or persisted.
        """
        return self._id

    @computed_field
    @property
    def element_id(self) -> Optional[str]:
        """
        Element ID of the database entity. Will be `None` as long as the model is **not hydrated
        or persisted**.
        For clients using `Memgraph`, this will be the same as `id`.

        Returns:
            Optional[str]: The Element ID or `None` if not hydrated or persisted.
        """
        return self._element_id

    def _compute_checksums(self) -> Dict[str, Optional[str]]:
        logger.debug("Computing checksums for model fields")
        checksums: Dict[str, Optional[str]] = {}

        for field_name in self.__class__.model_fields.keys():
            value = getattr(self, field_name)
            if value is None:
                checksums[field_name] = None
            else:
                dump = self.model_dump_json(include={field_name})
                checksums[field_name] = hashlib.blake2b(
                    dump.encode("utf-8"), usedforsecurity=False
                ).hexdigest()

        return checksums

    def _serialize(self, **kwargs) -> Dict[str, Any]:
        logger.debug("Serializing model to a storable format")
        return self.model_dump(by_alias=True, exclude={"element_id", "id"}, **kwargs)

    @classmethod
    def _deserialize(cls, obj: Dict[str, Any]) -> Self:
        deserialized: Dict[str, Any] = {}
        logger.debug("Deserializing stored object into model")

        for field_name, value in obj.items():
            resolved_field_name = cls._alias_cache.get(field_name) or field_name
            field_info = cls.model_fields.get(resolved_field_name)

            if field_info is None:
                logger.warning(
                    "Encountered unknown field %s for model %s, skipping",
                    field_name,
                    cls.__name__,
                )
                continue

            deserialized[field_name] = value

        return cls.model_validate(deserialized)
