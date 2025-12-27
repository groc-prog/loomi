from abc import ABC
from enum import StrEnum
from typing import (
    Any,
    Dict,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from neo4j import AsyncDriver, Driver
from neo4j.graph import Node, Path, Relationship

from loomi._logger import _LogContextKey, _scoped_log_ctx, logger
from loomi.models._base import LoomiBaseConfiguration
from loomi.models.node import LoomiNode
from loomi.models.path import LoomiPath
from loomi.models.relationship import LoomiRelationship

T = TypeVar("T", bound=Union[Driver, AsyncDriver])


class _ServerType(StrEnum):
    NEO4J = "Neo4j"
    MEMGRAPH = "Memgraph"


class _LoomiBaseClient(Generic[T], ABC):
    _driver: T
    _config: Optional[LoomiBaseConfiguration]
    _server_type: Optional[_ServerType]
    _server_version: Optional[Tuple[int, ...]]
    _models: Dict[str, Union[Type[LoomiNode], Type[LoomiRelationship]]]

    def __init__(self, driver: T, config: Optional[LoomiBaseConfiguration] = None):
        self._driver = driver
        self._config = config
        self._server_type = None
        self._server_version = None
        self._models = {}

    def register(
        self, *models: Union[Type[LoomiNode], Type[LoomiRelationship]]
    ) -> None:
        """
        Registers models with the current client. Models which have not been registered can not be
        resolved from query results.

        Args:
            *models (Union[Type[LoomiNode], Type[LoomiRelationship]]): The models to register.
        """
        with _scoped_log_ctx(
            {
                _LogContextKey.DRIVER: self._driver.__class__.__name__,
                _LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            for model in models:
                if not issubclass(model, (LoomiNode, LoomiRelationship)):
                    logger.warning(
                        (
                            "Invalid model %s provided during model registration. Class ",
                            "will be ignored",
                        ),
                        model.__name__,
                    )
                    return

                if model._hash is None:
                    logger.warning(
                        "Hash on model %s is not initialized yet. Model will be skipped",
                        model.__name__,
                    )
                    return

                logger.debug("Registering model %s with client %s", model, self)
                self._models[model._hash] = model

    def _extract_version(self, version: str) -> None:
        self._server_version = tuple(int(part) for part in version.split("."))

    def _transform_entity(self, entity: Any) -> Any:
        if isinstance(entity, (Node, Relationship)):
            return self._entity_to_model(entity)
        if isinstance(entity, Path):
            logger.debug("Transforming nodes and relationships from path %s", entity)
            return LoomiPath(
                tuple(self._entity_to_model(node) for node in entity.nodes),
                tuple(
                    self._entity_to_model(relationship)
                    for relationship in entity.relationships
                ),
                entity.graph,
            )

        logger.debug("Entity %s is a primitive value, skipping transformation", entity)
        return entity

    @overload
    def _entity_to_model(self, entity: Node) -> Union[LoomiNode, Node]: ...

    @overload
    def _entity_to_model(
        self, entity: Relationship
    ) -> Union[LoomiRelationship, Relationship]: ...

    def _entity_to_model(
        self, entity: Union[Node, Relationship]
    ) -> Union[LoomiNode, LoomiRelationship, Node, Relationship]:
        model_hash = (
            LoomiNode._generate_loomi_hash(list(entity.labels))
            if isinstance(entity, Node)
            else LoomiRelationship._generate_loomi_hash(entity.type)
        )

        if model_hash not in self._models:
            logger.warning(
                "No model with hash %s registered with client. Record will not be resolved "
                "to model",
                model_hash,
            )
            return entity

        model = self._models[model_hash]
        logger.debug("Transforming %s to model %s", entity, model.__name__)

        instance = model.model_validate(dict(entity))
        instance._id = entity.id
        instance._element_id = entity.element_id

        return instance

    def _relationship_type_to_model(
        self, type_: str
    ) -> Optional[Type[LoomiRelationship]]:
        model_hash = LoomiRelationship._generate_loomi_hash(type_)

        if model_hash not in self._models:
            logger.warning(
                "No model with hash %s registered with client. Record will not be resolved "
                "to model",
                model_hash,
            )
            return None

        return cast(Type[LoomiRelationship], self._models[model_hash])
