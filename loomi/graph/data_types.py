from datetime import date, datetime, time
from typing import Annotated, Any

import neo4j.time
from pydantic import GetJsonSchemaHandler, SerializationInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


class Neo4jTemporalDateAnnotation:
    """Pydantic annotation for `neo4j.time.Date`"""

    @classmethod
    def __get_pydantic_core_schema__(cls, *_) -> CoreSchema:
        def validate_from_date(value: date) -> neo4j.time.Date:
            return neo4j.time.Date(value.year, value.month, value.day)

        def serialize_date(value: neo4j.time.Date, info: SerializationInfo):
            if info.mode_is_json():
                return value.to_native()

            return value

        from_date_schema = core_schema.chain_schema(
            [
                core_schema.date_schema(),
                core_schema.no_info_plain_validator_function(validate_from_date),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_date_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(neo4j.time.Date), from_date_schema],
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_date, info_arg=True
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.date_schema())

    @classmethod
    def coerce(cls, value: Any) -> Any:
        """
        Utility method for coercing `neo4j.time.Date` objects to a Python native
        `datetime.date` object. Intended to be used with Pydantic validators.

        Args:
            value (Any): The value to try and coerce.

        Returns:
            The coerced value or the input value as-is if coercion is not possible.
        """
        if not isinstance(value, neo4j.time.Date):
            return value

        return value.to_native()


class Neo4jTemporalTimeAnnotation:
    """Pydantic annotation for `neo4j.time.Time`"""

    @classmethod
    def __get_pydantic_core_schema__(cls, *_) -> CoreSchema:
        def validate_from_time(value: time) -> neo4j.time.Time:
            return neo4j.time.Time(value.hour, value.minute, value.second, 0, value.tzinfo)

        def serialize_time(value: neo4j.time.Time, info: SerializationInfo):
            if info.mode_is_json():
                return value.to_native()

            return value

        from_time_schema = core_schema.chain_schema(
            [
                core_schema.time_schema(),
                core_schema.no_info_plain_validator_function(validate_from_time),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_time_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(neo4j.time.Time), from_time_schema],
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_time, info_arg=True
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.time_schema())

    @classmethod
    def coerce(cls, value: Any) -> Any:
        """
        Utility method for coercing `neo4j.time.Time` objects to a Python native
        `datetime.date` object. Intended to be used with Pydantic validators.

        Args:
            value (Any): The value to try and coerce.

        Returns:
            The coerced value or the input value as-is if coercion is not possible.
        """
        if not isinstance(value, neo4j.time.Time):
            return value

        return value.to_native()


class Neo4jTemporalDateTimeAnnotation:
    """Pydantic annotation for `neo4j.time.DateTime`"""

    @classmethod
    def __get_pydantic_core_schema__(cls, *_) -> CoreSchema:
        def validate_from_datetime(value: datetime) -> neo4j.time.DateTime:
            return neo4j.time.DateTime(
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                0,
                value.tzinfo,
            )

        def serialize_datetime(value: neo4j.time.DateTime, info: SerializationInfo):
            if info.mode_is_json():
                return value.to_native()

            return value

        from_datetime_schema = core_schema.chain_schema(
            [
                core_schema.datetime_schema(),
                core_schema.no_info_plain_validator_function(validate_from_datetime),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_datetime_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(neo4j.time.DateTime), from_datetime_schema],
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_datetime, info_arg=True
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.datetime_schema())

    @classmethod
    def coerce(cls, value: Any) -> Any:
        """
        Utility method for coercing `neo4j.time.DateTime` objects to a Python native
        `datetime.date` object. Intended to be used with Pydantic validators.

        Args:
            value (Any): The value to try and coerce.

        Returns:
            The coerced value or the input value as-is if coercion is not possible.
        """
        if not isinstance(value, neo4j.time.DateTime):
            return value

        return value.to_native()


Neo4jTemporalDate = Annotated[neo4j.time.Date, Neo4jTemporalDateAnnotation]
"""Pydantic compatible representation of neo4j.time.Date"""

Neo4jTemporalTime = Annotated[neo4j.time.Time, Neo4jTemporalTimeAnnotation]
"""Pydantic compatible representation of neo4j.time.Time"""

Neo4jTemporalDateTime = Annotated[neo4j.time.DateTime, Neo4jTemporalDateTimeAnnotation]
"""Pydantic compatible representation of neo4j.time.DateTime"""

# TODO: Implement remaining data types which are currently not supported by Pydantic
# See this Github issue: https://github.com/pydantic/pydantic/issues/11287
