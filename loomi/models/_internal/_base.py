# pylint: disable=arguments-differ

import datetime
import json
from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, Optional, Self, TypedDict, cast

import xxhash
from neo4j import spatial, time
from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field

from loomi._logger import _logger
from loomi.exceptions import SerializationError

if TYPE_CHECKING:
    from loomi.client._internal._base import LoomiClientConfiguration, _ServerType
else:
    _ServerType = object
    LoomiClientConfiguration = object

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

_SUPPORTED_LIST_DATA_TYPES = (
    bool,
    int,
    float,
    str,
    bytes,
    bytearray,
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
    serializer_fn: Callable[[Any], Any]
    """
    A custom function used when serializing nested objects before storing the model to the
    database. Defaults to `json.dumps` if not defined.

    [!NOTE] This function will be called for all properties which are not of a supported data type
    after `model.model_dump()` has been called.
    """

    deserializer_fn: Callable[[Any], Any]
    """
    A custom function used when de-serializing nested objects before passing the data to the
    Pydantic model. Defaults to `json.loads` if not defined.

    [!NOTE] This function will be called for all properties which do not match their annotation as
    defined on the model. For lists, this will be called for all list items.
    """


class _EntityBase(BaseModel, ABC):
    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)
    _checksums: Dict[str, Optional[str]] = PrivateAttr(default_factory=dict)
    _alias_cache: ClassVar[Dict[str, str]] = {}

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
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

    def _serialize(
        self, mode: _ServerType, client_config: LoomiClientConfiguration, **kwargs
    ) -> Dict[str, Any]:
        from loomi.client._internal._base import _ServerType

        model_dump = self.model_dump(by_alias=True, exclude={"element_id", "id"}, **kwargs)
        serialized: Dict[str, Any] = {}

        _logger.debug("Serializing model %s to a storable format", self)
        model_config = cast(_EntityConfiguration, getattr(self, "loomi_config", {}))

        serialize_nested = client_config.get("serialize_nested", False)
        serializer_fn = model_config.get("serializer_fn")
        if serializer_fn is None:
            raise SerializationError("No `serializer_fn` available")

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
                        serialized[field_name] = serializer_fn(value)
                        continue
                    except Exception as exc:
                        raise SerializationError(
                            f"Property {field_name} is not JSON serializable"
                        ) from exc

                if isinstance(value, list):
                    serialized_list = []

                    _logger.debug("Serializing list items for property %s", field_name)
                    for index, item in enumerate(value):
                        if not isinstance(item, _SUPPORTED_LIST_DATA_TYPES):
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
                                serialized_list.append(serializer_fn(item))
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
    def _deserialize(
        cls, obj: Dict[str, Any], mode: _ServerType, client_config: LoomiClientConfiguration
    ) -> Self:
        from loomi.client._internal._base import _ServerType

        deserialized: Dict[str, Any] = {}

        _logger.debug("Deserializing object to model instance")
        model_config = cast(_EntityConfiguration, getattr(cls, "loomi_config", {}))

        serialize_nested = client_config.get("serialize_nested", False)
        deserializer_fn = model_config.get("deserializer_fn")
        if deserializer_fn is None:
            raise SerializationError("No `deserializer_fn` available")

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
                        deserialized[field_name] = deserializer_fn(value)
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
                            deserializer_fn(item) for item in value if isinstance(item, str)
                        ]
                        continue
                    except Exception as exc:
                        raise SerializationError(
                            f"Stringified value at {field_name} is not valid JSON"
                        ) from exc

            deserialized[field_name] = value

        return cls.model_validate(deserialized)

    @classmethod
    def _init_config_defaults(cls) -> None:
        if "serializer_fn" not in cls.loomi_config:  # type: ignore
            cls.loomi_config["serializer_fn"] = json.dumps  # type: ignore

        if "deserializer_fn" not in cls.loomi_config:  # type: ignore
            cls.loomi_config["deserializer_fn"] = json.loads  # type: ignore
