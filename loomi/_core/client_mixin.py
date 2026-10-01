# pylint: disable=missing-class-docstring, missing-function-docstring

import functools
import inspect
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    overload,
)

import neo4j
import neo4j.graph

from loomi._core.types import ModelType
from loomi._logger import LogContext, logger, scoped_log_ctx
from loomi.constants import ServerType
from loomi.exceptions import ClientError, ModelError, SerializationError
from loomi.graph.node import Node
from loomi.graph.path import Path
from loomi.graph.relationship import Relationship

T = TypeVar("T", bound=Union[neo4j.Driver, neo4j.AsyncDriver])
U = TypeVar("U", bound=Callable[..., Any])


class ClientConfiguration(TypedDict, total=False):
    """TypedDict for configuring Loomi client behavior."""

    serialize_nested: bool
    """Whether nested properties should be serialized before they are stored to Neo4j."""

    strict_transformations: bool
    """
    Whether entities which can not be transformed to models should be kept unchanged or
    raise a exception.
    """


def require_server_metadata(func: U) -> U:
    exc = ClientError("Client must be initialized before method can be called")

    @functools.wraps(func)
    async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._server_type is None:
            raise exc
        return await func(self, *args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._server_type is None:
            raise exc
        return func(self, *args, **kwargs)

    if inspect.iscoroutinefunction(func):
        return cast(U, async_wrapper)
    return cast(U, sync_wrapper)


class ClientMixin(Generic[T]):
    _driver: T
    _server_type: Optional[ServerType]
    _server_version: Optional[Tuple[int, ...]]
    _models: Dict[str, ModelType]
    _configuration: ClientConfiguration

    def __init__(self, driver: T, **config):
        self._driver = driver
        self._server_type = None
        self._server_version = None
        self._models = {}
        self._configuration = self.__init_configuration(**config)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} driver={self._driver.__class__.__name__} "
            f"server_type={self._server_type} server_version={self._server_version}>"
        )

    def server_type(self) -> Optional[ServerType]:
        """
        Returns the type of server the client is currently connected to.

        Returns:
            Optional[ServerType]: The server type or `None` if client is not yet connected.
        """
        return self._server_type

    def register(self, *models: ModelType) -> None:
        """
        Registers models with the current client. Models which have not been registered can not be
        resolved from query results.

        Args:
            *models (ModelType): The models to register.

        Raises:
            ModelError: If a model has not finished initialization.
        """
        with scoped_log_ctx({LogContext.DRIVER: self._driver.__class__.__name__}):
            for model in models:
                if not issubclass(model, (Node, Relationship)):
                    logger.warning(
                        "Invalid model %s provided during model registration, skipping",
                        model,
                    )
                    continue

                # In most cases, the hash should always be initialized, but there can be some cases in which
                # the models have not finished initialization
                if model._hash is None:
                    raise ModelError(
                        f"Hash on model {model.__name__} is not initialized. Maybe you forgot to "
                        f"call {model.model_rebuild.__name__}?"
                    )

                logger.debug("Registering model %s with client %s", model, self)
                self._models[model._hash] = model

    def _extract_version(self, version: str) -> None:
        self._server_version = tuple(int(part) for part in version.split("."))

    def _transform_entity(self, entity: Any) -> Any:
        with scoped_log_ctx(
            {
                LogContext.DRIVER: self._driver.__class__.__name__,
                LogContext.SERVER_TYPE: self._server_type,
            }
        ):
            if isinstance(entity, (neo4j.graph.Node, neo4j.graph.Relationship)):
                return self._entity_to_model(entity)
            if isinstance(entity, neo4j.graph.Path):
                logger.debug("Transforming nodes and relationships from path %s", entity)
                return Path(
                    self,
                    tuple(self._entity_to_model(node) for node in entity.nodes),
                    tuple(
                        self._entity_to_model(relationship) for relationship in entity.relationships
                    ),
                    entity.graph,
                )

            logger.debug("Entity %s is a primitive value, skipping transformation", entity)
            return entity

    @overload
    def _entity_to_model(self, entity: neo4j.graph.Node) -> Union[Node, neo4j.graph.Node]: ...

    @overload
    def _entity_to_model(
        self, entity: neo4j.graph.Relationship
    ) -> Union[Relationship, neo4j.graph.Relationship]: ...

    def _entity_to_model(
        self, entity: Union[neo4j.graph.Node, neo4j.graph.Relationship]
    ) -> Union[Node, Relationship, neo4j.graph.Node, neo4j.graph.Relationship]:
        is_node = isinstance(entity, neo4j.graph.Node)

        model_hash = (
            Node._generate_hash(list(entity.labels))
            if is_node
            else Relationship._generate_hash(entity.type)
        )

        if model_hash not in self._models:
            identifiers = f"labels {", ".join(entity.labels)}" if is_node else f"type {entity.type}"

            if self._configuration.get("strict_transformations"):
                raise SerializationError(f"No model with {identifiers} registered")

            logger.warning(
                "No model with %s registered with client. Record will not be transformed",
                identifiers,
            )
            return entity

        model = self._models[model_hash]
        logger.debug("Transforming %s to model %s", entity, model.__name__)

        instance = model._deserialize(
            dict(entity), self._server_type or ServerType.NEO4J, self._configuration
        )
        instance._id = entity.id
        instance._element_id = entity.element_id

        return instance

    def _relationship_type_to_model(self, type_: str) -> Optional[Type[Relationship]]:
        with scoped_log_ctx(
            {
                LogContext.DRIVER: self._driver.__class__.__name__,
                LogContext.SERVER_TYPE: self._server_type,
            }
        ):
            model_hash = Relationship._generate_hash(type_)

            if model_hash not in self._models:
                if self._configuration.get("strict_transformations"):
                    raise SerializationError(f"No model with type {type_} registered")

                logger.warning(
                    "No model with type %s registered with client. Record will not be transformed",
                    type_,
                )
                return None

            return cast(Type[Relationship], self._models[model_hash])

    def __init_configuration(self, **config) -> ClientConfiguration:
        return ClientConfiguration(
            serialize_nested=config.get("serialize_nested", False),
            strict_transformations=config.get("strict_transformations", True),
        )
