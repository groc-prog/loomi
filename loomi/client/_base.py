from abc import ABC
from enum import StrEnum
from typing import Any, Dict, Optional, Tuple, Type, Union, cast, overload

from neo4j.graph import Node, Path, Relationship

from loomi._logger import logger
from loomi.models.base import LoomiBaseConfiguration
from loomi.models.node import LoomiNode
from loomi.models.path import LoomiPath
from loomi.models.relationship import LoomiRelationship


class _ServerType(StrEnum):
    NEO4J = "Neo4j"
    MEMGRAPH = "Memgraph"


class _LoomiBaseClient(ABC):
    _config: Optional[LoomiBaseConfiguration]
    _server_type: Optional[_ServerType]
    _server_version: Optional[Tuple[int, ...]]
    _models: Dict[str, Union[LoomiNode, LoomiRelationship]]

    def __init__(self, config: Optional[LoomiBaseConfiguration] = None):
        self._config = config
        self._server_type = None
        self._server_version = None
        self._models = {}

    def _extract_version(self, version: str) -> None:
        self._server_version = tuple(int(part) for part in version.split("."))

    def _register_model(
        self, model: Union[Type[LoomiNode], Type[LoomiRelationship]]
    ) -> None:
        if not issubclass(model, (LoomiNode, LoomiRelationship)):
            logger.warning(
                "Invalid model %s provided during model registration. Class will be ignored",
                model.__name__,
            )
            return

        if model._hash is None:
            logger.warning(
                "Hash on model %s is not initialized yet. Model will be skipped",
                model.__name__,
            )
            return

        self._models[model._hash] = model

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
                "Model with hash %s is not registered with client. Record will not be resolved "
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

    def _type_to_model(self, type_: str) -> Optional[Type[LoomiRelationship]]:
        model_hash = LoomiRelationship._generate_loomi_hash(type_)

        if model_hash not in self._models:
            logger.warning(
                "Model with hash %s is not registered with client. Record will not be resolved "
                "to model",
                model_hash,
            )
            return None

        return cast(Type[LoomiRelationship], self._models[model_hash])
