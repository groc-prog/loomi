# pylint: disable=arguments-differ, missing-class-docstring

import json
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Self,
    TypedDict,
    cast,
)

import xxhash
from pydantic import BaseModel, ConfigDict, PrivateAttr, computed_field

from loomi._internal._types import ModelType
from loomi._logger import LogContextKey, logger, scoped_log_ctx
from loomi.constants import SUPPORTED_DATA_TYPES, SUPPORTED_LIST_DATA_TYPES, ServerType
from loomi.exceptions import SerializationError
from loomi.query.descriptor import PropertyDescriptor

if TYPE_CHECKING:
    from loomi._internal._base_client import ClientConfiguration
else:
    ClientConfiguration = object


class EntityConfiguration(TypedDict, total=False):
    serializer_fn: Callable[[Any], Any]
    """
    A custom function used when serializing nested objects before storing the model to the
    database. Defaults to `json.dumps` if not defined.

    [!NOTE] This function will be called for all properties which are not included in
    `SUPPORTED_DATA_TYPES` after `model.model_dump()` has been called.
    """

    deserializer_fn: Callable[[Any], Any]
    """
    A custom function used when de-serializing nested objects before passing the data to the
    Pydantic model. Defaults to `json.loads` if not defined.

    [!NOTE] This function will be called for all properties which do not match their annotation as
    defined on the model. For lists, this will be called for all list items.
    """


class EntityBaseMetaclass(type(BaseModel)):
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
                return PropertyDescriptor(name, model_fields[name].annotation, cast(ModelType, cls))

        return super().__getattribute__(name)


class EntityBase(BaseModel, metaclass=EntityBaseMetaclass):
    _id: Optional[int] = PrivateAttr(None)
    _element_id: Optional[str] = PrivateAttr(None)
    _hash: Optional[str] = PrivateAttr(None)
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
            Optional[int]: The Element ID or `None` if not hydrated or persisted.
        """
        return self._element_id

    def _compute_checksums(self) -> Dict[str, Optional[str]]:
        with scoped_log_ctx(
            {
                LogContextKey.MODEL_NAME: self.__class__.__name__,
                LogContextKey.MODEL_IDENTIFIER: self._hash,
            }
        ):
            logger.debug("Computing checksums for model fields")
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
        self, mode: ServerType, client_config: ClientConfiguration, **kwargs
    ) -> Dict[str, Any]:
        with scoped_log_ctx(
            {
                LogContextKey.MODEL_NAME: self.__class__.__name__,
                LogContextKey.MODEL_IDENTIFIER: self._hash,
            }
        ):
            model_dump = self.model_dump(by_alias=True, exclude={"element_id", "id"}, **kwargs)
            serialized: Dict[str, Any] = {}

            model_config = cast(EntityConfiguration, getattr(self, "loomi_config", {}))

            serialize_nested = client_config.get("serialize_nested", False)
            serializer_fn = model_config.get("serializer_fn")
            if serializer_fn is None:
                raise SerializationError("No `serializer_fn` available")

            logger.debug(
                "Serializing model to a storable format with 'serialize_nested' set to %s",
                serialize_nested,
            )
            for field_name, value in model_dump.items():
                if not isinstance(value, SUPPORTED_DATA_TYPES):
                    raise SerializationError(
                        f"Data type {type(value)} can not be stored. Supported data types are "
                        f"{", ".join(data_type.__name__ for data_type in SUPPORTED_DATA_TYPES)}"
                    )

                # If mode is Neo4j and we encounter nested values, we either need to raise a exception
                # or serialize the value if configured
                if mode == ServerType.NEO4J:
                    if isinstance(value, dict):
                        serialized[field_name] = self._serialize_neo4j_dict(
                            field_name, value, serializer_fn, serialize_nested
                        )
                        continue

                    if isinstance(value, list):
                        serialized[field_name] = self._serialize_neo4j_list(
                            field_name, value, serializer_fn, serialize_nested
                        )
                        continue

                serialized[field_name] = value

            return serialized

    def _serialize_neo4j_dict(
        self,
        field_name: str,
        value: Any,
        serializer_fn: Callable[[Any], Any],
        serialize_nested: bool,
    ) -> Any:
        if not serialize_nested:
            raise SerializationError(
                "Nested data types are only supported if `serialize_nested` is "
                f"enabled. The nested property was found at "
                f"{self.__class__.__name__}.{field_name}"
            )

        try:
            logger.debug("Serializing nested property %s", field_name)
            return serializer_fn(value)
        except Exception as exc:
            raise SerializationError(f"Property {field_name} is not serializable") from exc

    def _serialize_neo4j_list(
        self,
        field_name: str,
        value: Any,
        serializer_fn: Callable[[Any], Any],
        serialize_nested: bool,
    ) -> List[Any]:
        serialized_list = []

        logger.debug("Serializing list items for property %s", field_name)
        for index, item in enumerate(value):
            if not isinstance(item, SUPPORTED_LIST_DATA_TYPES):
                if not serialize_nested:
                    raise SerializationError(
                        "Nested data types are only supported if `serialize_nested` "
                        "is enabled. The nested property was found at "
                        f"{self.__class__.__name__}.{field_name}[{index}]"
                    )

                try:
                    logger.debug("Serializing nested property %s at index %d", field_name, index)
                    serialized_list.append(serializer_fn(item))
                    continue
                except Exception as exc:
                    raise SerializationError(
                        f"Property {field_name}[{index}] is not serializable"
                    ) from exc

            serialized_list.append(item)

        return serialized_list

    @classmethod
    def _deserialize(
        cls, obj: Dict[str, Any], mode: ServerType, client_config: ClientConfiguration
    ) -> Self:
        with scoped_log_ctx(
            {
                LogContextKey.MODEL_NAME: cls.__name__,
                LogContextKey.MODEL_IDENTIFIER: cls._hash,
            }
        ):
            deserialized: Dict[str, Any] = {}
            model_config = cast(EntityConfiguration, getattr(cls, "loomi_config", {}))

            serialize_nested = client_config.get("serialize_nested", False)
            deserializer_fn = model_config.get("deserializer_fn")
            if deserializer_fn is None:
                raise SerializationError(
                    "No `deserializer_fn` available. Maybe you forgot to "
                    f"call {cls.model_rebuild.__name__}?"
                )

            logger.debug(
                "Deserializing stored object into model with 'serialize_nested' set to %s",
                serialize_nested,
            )
            for field_name, value in obj.items():
                resolved_field_name = cls._alias_cache.get(field_name) or field_name
                field_info = cls.model_fields.get(resolved_field_name)

                if field_info is None:
                    logger.warning("Encountered unknown property %s, skipping", field_name)
                    continue

                # Some values might have been stringified previously, so we need to check each of
                # them and deserialize them back to a dictionary so Pydantic can handle the rest of
                # the validation correctly
                if mode == ServerType.NEO4J and serialize_nested and isinstance(value, (str, list)):
                    if isinstance(value, str) and field_info.annotation is not str:
                        try:
                            logger.debug(
                                (
                                    "Stringified value found at %s, parsing value with "
                                    "'deserializer_fn'"
                                ),
                                field_name,
                            )
                            deserialized[field_name] = deserializer_fn(value)
                            continue
                        except Exception as exc:
                            raise SerializationError(
                                f"Serialized value at {field_name} could not be deserialized"
                            ) from exc

                    if isinstance(value, list):
                        try:
                            logger.debug(
                                "Deserializing list items at property %s",
                                field_name,
                            )

                            deserialized_list = []
                            for index, item in enumerate(value):
                                if not isinstance(item, str):
                                    deserialized_list.append(item)
                                    continue

                                logger.debug(
                                    "Possibly stringified value found for property %s at index %d",
                                    field_name,
                                    index,
                                )
                                deserialized_list.append(deserializer_fn(item))

                            deserialized[field_name] = deserialized_list
                            continue
                        except Exception as exc:
                            raise SerializationError(
                                f"Serialized value at {field_name} could not be deserialized"
                            ) from exc

                deserialized[field_name] = value

            return cls.model_validate(deserialized)

    @classmethod
    def _init_config_defaults(cls) -> None:
        with scoped_log_ctx(
            {
                LogContextKey.MODEL_NAME: cls.__name__,
                LogContextKey.MODEL_IDENTIFIER: cls._hash,
            }
        ):
            # `loomi_config` is defined per model class to prevent having to cast the type each time
            if "serializer_fn" not in cls.loomi_config:  # type: ignore
                logger.debug("No 'serializer_fn' defined, falling back to 'json.dumps'")
                cls.loomi_config["serializer_fn"] = json.dumps  # type: ignore

            if "deserializer_fn" not in cls.loomi_config:  # type: ignore
                logger.debug("No 'deserializer_fn' defined, falling back to 'json.loads'")
                cls.loomi_config["deserializer_fn"] = json.loads  # type: ignore
