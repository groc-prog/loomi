# pylint: disable=arguments-differ

import datetime
import json
from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Self, TypedDict, cast

import xxhash
from neo4j import spatial, time
from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field

from loomi._logger import _logger
from loomi.exceptions import ModelError, SerializationError

if TYPE_CHECKING:
    from loomi.client._internal._base import _ServerType
else:
    _ServerType = object

_SUPPORTED_DATA_TYPES = (
    bool,
    int,
    float,
    str,
    bytes,
    bytearray,
    list,
    dict,
    type(None),
    time.Date,
    time.Time,
    time.DateTime,
    time.Duration,
    spatial.Point,
    datetime.date,
    datetime.time,
    datetime.datetime,
    datetime.timedelta,
)


class _EntityConfiguration(TypedDict, total=False):
    serialize_nested: bool


class _EntityBase(BaseModel, ABC):
    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)
    _checksums: Dict[str, Optional[str]] = PrivateAttr(default_factory=dict)
    _alias_cache: ClassVar[Dict[str, str]] = {}

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        reserved_fields = ["all_", "any_"]

        for reserved in reserved_fields:
            if reserved in cls.model_fields:
                raise ModelError(f"{reserved} is a reserved field. Rename or remove it")

        for field_name, field_info in cls.model_fields.items():
            if field_info.alias is not None:
                cls._alias_cache[field_info.alias] = field_name

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
                dump = self.model_dump_json(include={field_name})
                checksums[field_name] = xxhash.xxh64(dump).hexdigest()

        return checksums

    def _serialize(self, mode: _ServerType) -> Dict[str, Any]:
        from loomi.client._internal._base import _ServerType

        model_dump = self.model_dump(by_alias=True, exclude={"element_id", "id"})
        serialized: Dict[str, Any] = {}

        _logger.debug("Serializing model %s to a storable format", self)
        config = cast(_EntityConfiguration, getattr(self, "loomi_config", {}))
        serialize_nested = config.get("serialize_nested", False)

        for field_name, value in model_dump.items():
            if not isinstance(value, _SUPPORTED_DATA_TYPES):
                raise SerializationError(
                    f"Data type {type(value)} can not be stored. Supported data types are "
                    f"{", ".join(_SUPPORTED_DATA_TYPES)}"
                )

            # If mode is Neo4j and we encounter nested values, we either need to raise a exception
            # or serialize the value if configured
            if mode == _ServerType.NEO4J:
                if isinstance(value, dict):
                    if not serialize_nested:
                        raise SerializationError(
                            "Nested data types are only supported if `serialize_nested` is "
                            f"enabled. The nested property was found at "
                            f"{self.__class__.__name__}.{field_name}"
                        )

                    try:
                        _logger.debug("Serializing nested property %s", field_name)
                        serialized[field_name] = json.dumps(value)
                        continue
                    except Exception as exc:
                        raise SerializationError(
                            f"Property {field_name} is not JSON serializable"
                        ) from exc

                if isinstance(value, list):
                    serialized_list = []

                    _logger.debug("Serializing list items for property %s", field_name)
                    for index, item in enumerate(value):
                        if isinstance(item, dict):
                            if not serialize_nested:
                                raise SerializationError(
                                    "Nested data types are only supported if `serialize_nested` "
                                    "is enabled. The nested property was found at "
                                    f"{self.__class__.__name__}.{field_name}[{index}]"
                                )

                            try:
                                _logger.debug(
                                    "Serializing nested property %s", f"{field_name}[{index}]"
                                )
                                serialized_list.append(json.dumps(item))
                                continue
                            except Exception as exc:
                                raise SerializationError(
                                    f"Property {field_name}[{index}] is not JSON serializable"
                                ) from exc

                        serialized_list.append(item)

                    serialized[field_name] = serialized_list
                    continue

            serialized[field_name] = value

        return serialized

    @classmethod
    def _deserialize(cls, obj: Dict[str, Any], mode: _ServerType) -> Self:
        from loomi.client._internal._base import _ServerType

        deserialized: Dict[str, Any] = {}

        _logger.debug("Deserializing object to model instance")
        config = cast(_EntityConfiguration, getattr(cls, "loomi_config", {}))
        serialize_nested = config.get("serialize_nested", False)

        for field_name, value in obj.items():
            resolved_field_name = cls._alias_cache.get(field_name) or field_name
            field_info = cls.model_fields.get(resolved_field_name)

            if field_info is None:
                _logger.warning("Encountered unknown property %s, skipping", field_name)
                continue

            # Some values might have been stringified previously, so we need to check each of
            # them and deserialize them back to a dictionary so Pydantic can handle the rest of
            # the validation correctly
            if mode == _ServerType.NEO4J and serialize_nested and isinstance(value, (str, list)):
                if isinstance(value, str) and field_info.annotation is not str:
                    try:
                        _logger.debug("Deserializing stringified property %s", field_name)
                        deserialized[field_name] = json.loads(value)
                        continue
                    except Exception as exc:
                        raise SerializationError(
                            f"Stringified value at {field_name} is not valid JSON"
                        ) from exc

                if isinstance(value, list):
                    try:
                        _logger.debug(
                            "Deserializing possibly stringified list items at property %s",
                            field_name,
                        )
                        deserialized[field_name] = [
                            json.loads(item) for item in value if isinstance(item, str)
                        ]
                        continue
                    except Exception as exc:
                        raise SerializationError(
                            f"Stringified value at {field_name} is not valid JSON"
                        ) from exc

            deserialized[field_name] = value

        return cls.model_validate(deserialized, by_alias=True)
