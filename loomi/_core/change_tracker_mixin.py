from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
    overload,
)

import neo4j

from loomi.constants import ServerType
from loomi.exceptions import ChangeTrackerError, ModelError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.logger import get_logger

if TYPE_CHECKING:
    from loomi._async.client import AsyncClient
    from loomi._sync.client import Client
else:
    AsyncClient = object
    Client = object

T = TypeVar(
    "T", bound=Union[neo4j.Session, neo4j.AsyncSession, neo4j.Transaction, neo4j.AsyncTransaction]
)

TrackedEntity = Union[Node, Relationship]
EntityStateType = Literal["nodes", "relationships"]

logger = get_logger("change_tracker")


class NodeInsertItem(TypedDict):
    id_: int
    properties: Dict[str, Any]


class NodeInsertBatch(TypedDict):
    labels: Set[str]
    batches: List[NodeInsertItem]


class RelationshipInsertItem(TypedDict):
    start_node_id: Union[str, int]
    end_node_id: Union[str, int]
    properties: Dict[str, Any]


class RelationshipInsertBatch(TypedDict):
    type_: str
    batches: List[RelationshipInsertItem]


class EntityUpdateBatch(TypedDict):
    id_: Union[str, int]
    properties: Dict[str, Any]


class TrackingOperation(Enum):
    ADD = 0
    DELETE = 1
    UPDATE = 2


class TrackingOperationState(TypedDict):
    nodes: Dict[int, Tuple[Node, Dict[str, Optional[str]]]]
    relationships: Dict[int, Tuple[Relationship, Dict[str, Optional[str]]]]


class ChangeTrackerMixin(Generic[T]):
    _state: Dict[TrackingOperation, TrackingOperationState]
    _grouping_map: Dict[int, Tuple[int, int]]
    _session_or_tx: T
    _client: Union[Client, AsyncClient]

    def __init__(self, session_or_tx: T, client: Union[Client, AsyncClient]):
        self.__set_initial_state()
        self._session_or_tx = session_or_tx
        self._client = client

    @overload
    def add(self, model: Node) -> None: ...

    @overload
    def add(
        self,
        model: Relationship,
        start_node: Optional[Node] = None,
        end_node: Optional[Node] = None,
    ) -> None: ...

    def add(
        self,
        model: TrackedEntity,
        start_node: Optional[Node] = None,
        end_node: Optional[Node] = None,
    ) -> None:
        """
        Starts tracking a saved or unsaved entity in the change tracker. Depending on whether
        the entity has been saved or not, it will either be updated or created when `.flush()`
        is called.

        Args:
            model (TrackedEntity): The entity to start tracking.
            start_node (TrackedEntity): The start node of the current relationship. Required if
                the tracked relationship is not saved yet.
            end_node (TrackedEntity): The end node of the current relationship. Required if
                the tracked relationship is not saved yet.

        Raises:
            ChangeTrackerError: If the start/end node is missing when tracking a unsaved relationship.
        """
        self.__track_entity(model)

        if isinstance(model, Relationship):
            is_saved = self.__get_entity_saved(model)
            if not is_saved and (start_node is None or end_node is None):
                raise ChangeTrackerError(
                    "Both start and end nodes have to be defined when tracking a unsaved "
                    "relationship"
                )

            if start_node is not None:
                logger.debug("Adding start node for relationship to change tracker")
                self.__track_entity(start_node)

            if end_node is not None:
                logger.debug("Adding end node for relationship to change tracker")
                self.__track_entity(end_node)

            if not is_saved:
                # Remember the dependencies between relationship and nodes to be able to resolve
                # the queries later on
                self._grouping_map[self.__get_entity_identifier(model)] = (
                    self.__get_entity_identifier(cast(TrackedEntity, start_node)),
                    self.__get_entity_identifier(cast(TrackedEntity, end_node)),
                )

    def delete(self, model: TrackedEntity) -> None:
        """
        Marks a entity to be deleted by the change tracker. If the entity has not been saved to
        the database yet, it will be skipped.

        Args:
            model (TrackedEntity): The entity to mark to be deleted.
        """
        identifier = self.__get_entity_identifier(model)
        entity_type = self.__get_entity_type(model)
        is_saved = self.__get_entity_saved(model)
        current_tracking_operation = self.__get_current_tracking_operation(identifier, entity_type)

        if is_saved and current_tracking_operation == TrackingOperation.DELETE:
            logger.debug(
                "Entity %d is already being tracking in state %s for entity type %s",
                identifier,
                current_tracking_operation,
                entity_type,
            )
            return

        if current_tracking_operation is not None:
            self.__remove_tracking_state(identifier, current_tracking_operation, entity_type)

        if not is_saved:
            logger.debug(
                "Entity %d is not saved to the database yet, omitting entity from change tracker",
                identifier,
            )
            # Unsaved entities can not be deleted, so there is nothing to do here
            return

        self.__set_tracking_state(model, identifier, TrackingOperation.DELETE)

    def detach(self, model: TrackedEntity) -> None:
        """
        Removes a previously tracked entity from the change tracker.

        Args:
            model (TrackedEntity): The entity to no longer track.
        """
        identifier = self.__get_entity_identifier(model)
        entity_type = self.__get_entity_type(model)

        logger.debug(
            "Removing entity %d in state type %s from change tracker", identifier, entity_type
        )
        for operation in TrackingOperation:
            removed = self._state[operation][entity_type].pop(identifier, None)

            if removed is not None:
                logger.debug(
                    "Removed entity %d from state with tracking operation %s", identifier, operation
                )

        if isinstance(model, Relationship) and identifier in self._grouping_map:
            logger.debug(
                "Detached entity %d is a relationship with start and end nodes. Removing relationship "
                "grouping from state tracking",
                identifier,
            )
            self._grouping_map.pop(identifier)

    def clear(self) -> None:
        """
        Clears all currently tracked entities from the change tracker. This is automatically called after
        `.flush()` is called.
        """
        count_add_entities = len(self._state[TrackingOperation.ADD]["nodes"]) + len(
            self._state[TrackingOperation.ADD]["relationships"]
        )
        count_update_entities = len(self._state[TrackingOperation.UPDATE]["nodes"]) + len(
            self._state[TrackingOperation.UPDATE]["relationships"]
        )
        count_delete_entities = len(self._state[TrackingOperation.DELETE]["nodes"]) + len(
            self._state[TrackingOperation.DELETE]["relationships"]
        )
        logger.debug(
            "Clearing change tracker; %s entities: %d; %s entities: %d; %s entities: %d",
            TrackingOperation.ADD,
            count_add_entities,
            TrackingOperation.UPDATE,
            count_update_entities,
            TrackingOperation.DELETE,
            count_delete_entities,
        )
        self.__set_initial_state()

    def _omit_redundant_relationship_operations(self) -> None:
        if not self._grouping_map:
            return

        logger.debug("Omitting redundant operations for relationships")

        add_nodes = self._state[TrackingOperation.ADD]["nodes"]
        update_nodes = self._state[TrackingOperation.UPDATE]["nodes"]
        relevant_nodes = add_nodes.keys() | update_nodes.keys()
        add_relationships = self._state[TrackingOperation.ADD]["relationships"]
        update_relationships = self._state[TrackingOperation.UPDATE]["relationships"]

        # Check if any of the grouped entities are no longer relevant, for example a relationship
        # was marked to be created, but the start/end node is being deleted
        for relationship_id, (start_node_id, end_node_id) in self._grouping_map.items():
            if start_node_id not in relevant_nodes or end_node_id not in relevant_nodes:
                add_relationships.pop(relationship_id, None)
                update_relationships.pop(relationship_id, None)

    def _build_node_add_operations(self) -> List[Tuple[str, Dict[str, Any]]]:
        add_nodes = self._state[TrackingOperation.ADD]["nodes"]
        if not add_nodes:
            logger.debug("No added nodes to build queries for, skipping")
            return []

        server_type = cast(ServerType, self._client._server_type)
        groups: Dict[str, NodeInsertBatch] = {}
        logger.debug(
            "Compiling queries for node entities with operation type %s", TrackingOperation.ADD.name
        )

        # Since we can not define labels with parameters, we have to build a separate query for
        # each label combination
        for obj_id, (reference, _) in add_nodes.items():
            hash_ = reference._hash
            if hash_ is None:
                raise ModelError(
                    f"Hash on model {reference.__class__.__name__} is not initialized. Maybe you "
                    f"forgot to call {reference.model_rebuild.__name__}?"
                )

            groups.setdefault(hash_, {"labels": reference.labels(), "batches": []})[
                "batches"
            ].append({"id_": obj_id, "properties": reference._serialize()})

        entity_identifier = "elementId(e)" if server_type == ServerType.NEO4J else "id(e)"
        return [
            (
                f"UNWIND $p0 AS r CREATE (e:{':'.join(group['labels'])}) "
                f"SET e = r.properties RETURN r.id_, {entity_identifier}",
                {"p0": group["batches"]},
            )
            for group in groups.values()
        ]

    def _build_relationship_add_operations(
        self, id_map: Dict[int, Union[str, int]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        add_relationships = self._state[TrackingOperation.ADD]["relationships"]
        if not add_relationships:
            logger.debug("No added relationships to build queries for, skipping")
            return []

        server_type = cast(ServerType, self._client._server_type)
        groups: Dict[str, RelationshipInsertBatch] = {}
        logger.debug(
            "Compiling queries for relationship entities with operation type %s",
            TrackingOperation.ADD.name,
        )

        for obj_id, (reference, _) in add_relationships.items():
            hash_ = reference._hash
            if hash_ is None:
                raise ModelError(
                    f"Hash on model {reference.__class__.__name__} is not initialized. Maybe you "
                    f"forgot to call {reference.model_rebuild.__name__}?"
                )

            # Since relationships must define a start and end node when they are created, we have
            # to create them separately from the nodes so that we can reference the start and end
            # nodes with their ID's
            start_node_id, end_node_id = self._grouping_map[obj_id]
            group = groups.setdefault(hash_, {"type_": reference.type(), "batches": []})
            group["batches"].append(
                {
                    "start_node_id": self.__resolve_node_entity_id(start_node_id, id_map, "Start"),
                    "end_node_id": self.__resolve_node_entity_id(end_node_id, id_map, "End"),
                    "properties": reference._serialize(),
                }
            )

        entity_identifier = "elementId" if server_type == ServerType.NEO4J else "id"
        return [
            (
                f"UNWIND $p0 AS r "
                f"MATCH (n) WHERE {entity_identifier}(n) = r.start_node_id "
                f"MATCH (m) WHERE {entity_identifier}(m) = r.end_node_id "
                f"CREATE (n)-[e:{g['type_']}]->(m) "
                f"SET e = r.properties",
                {"p0": g["batches"]},
            )
            for g in groups.values()
        ]

    def _build_node_update_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not self._state[TrackingOperation.UPDATE]["nodes"]:
            logger.debug("No updated nodes to build queries for, skipping")
            return None

        batches = self.__build_update_batches("nodes")
        if batches is None:
            return None

        entity_identifier = (
            "elementId(e)" if self._client._server_type == ServerType.NEO4J else "id(e)"
        )
        return (
            f"UNWIND $p0 AS r MATCH (e) WHERE {entity_identifier} = r.id_ SET e += r.properties",
            {"p0": batches},
        )

    def _build_relationship_update_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not self._state[TrackingOperation.UPDATE]["relationships"]:
            logger.debug("No updated relationships to build queries for, skipping")
            return None

        batches = self.__build_update_batches("relationships")
        if batches is None:
            return None

        entity_identifier = (
            "elementId(e)" if self._client._server_type == ServerType.NEO4J else "id(e)"
        )
        return (
            f"UNWIND $p0 AS r MATCH ()-[e]->() WHERE {entity_identifier} = r.id_ SET e += r.properties",
            {"p0": batches},
        )

    def _build_node_delete_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not self._state[TrackingOperation.DELETE]["nodes"]:
            logger.debug("No deleted nodes to build queries for, skipping")
            return None

        ids = self.__build_delete_ids("nodes")
        entity_identifier = (
            "elementId(e)" if self._client._server_type == ServerType.NEO4J else "id(e)"
        )
        return (
            f"UNWIND $p0 AS r MATCH (e) WHERE {entity_identifier} = r DETACH DELETE e",
            {"p0": ids},
        )

    def _build_relationship_delete_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not self._state[TrackingOperation.DELETE]["relationships"]:
            logger.debug("No deleted relationships to build queries for, skipping")
            return None

        ids = self.__build_delete_ids("relationships")
        entity_identifier = (
            "elementId(e)" if self._client._server_type == ServerType.NEO4J else "id(e)"
        )
        return (
            f"UNWIND $p0 AS r MATCH ()-[e]->() WHERE {entity_identifier} = r DELETE e",
            {"p0": ids},
        )

    def __build_delete_ids(self, entity_type: EntityStateType) -> List[Union[str, int]]:
        server_type = self._client._server_type
        use_element_id = server_type == ServerType.NEO4J
        ids = []

        for reference, _ in self._state[TrackingOperation.DELETE][entity_type].values():
            if reference._element_id is None or reference._id is None:
                raise ChangeTrackerError(
                    f"Entity is being tracked as {TrackingOperation.DELETE.name} but has not "
                    "been saved to the database yet"
                )
            ids.append(reference._element_id if use_element_id else reference._id)

        return ids

    def __build_update_batches(
        self, entity_type: EntityStateType
    ) -> Optional[List[EntityUpdateBatch]]:
        batches: List[EntityUpdateBatch] = []
        server_type = cast(ServerType, self._client._server_type)

        for reference, original_checksums in self._state[TrackingOperation.UPDATE][
            entity_type
        ].values():
            if reference._element_id is None or reference._id is None:  # pragma: no cover
                raise ChangeTrackerError(
                    f"Entity is being tracked as {TrackingOperation.UPDATE.name} but has not "
                    "been saved to the database yet"
                )

            updated_checksums = reference._compute_checksums()
            changed_fields = [
                name
                for name, checksum in updated_checksums.items()
                if checksum not in (original_checksums[name], None)
            ]

            if not changed_fields:
                continue

            logger.debug(
                "Found %d changed properties for model %s",
                len(changed_fields),
                reference._element_id,
            )
            batches.append(
                {
                    "id_": (
                        reference._element_id if server_type == ServerType.NEO4J else reference._id
                    ),
                    "properties": reference._serialize(include=changed_fields),
                }
            )

        if len(batches) == 0:
            return None

        return batches

    def __resolve_node_entity_id(
        self,
        node_id: int,
        id_map: Dict[int, Union[str, int]],
        role: str,
    ) -> Union[str, int]:
        if node_id in id_map:
            return id_map[node_id]

        state = self._state[TrackingOperation.UPDATE]["nodes"].get(node_id)
        if state is None:  # pragma: no cover
            raise ChangeTrackerError(f"{role} node for relationship not found in change tracker")

        node, _ = state
        node_entity_id = (
            node._element_id if self._client._server_type == ServerType.NEO4J else node._id
        )

        if node_entity_id is None:  # pragma: no cover
            raise ChangeTrackerError(
                f"{role} node for relationship is being tracked as "
                f"{TrackingOperation.UPDATE.name} but is not saved to database"
            )

        return node_entity_id

    def __track_entity(self, model: TrackedEntity) -> None:
        identifier = self.__get_entity_identifier(model)
        entity_type = self.__get_entity_type(model)
        is_saved = self.__get_entity_saved(model)
        current_tracking_operation = self.__get_current_tracking_operation(identifier, entity_type)

        if (not is_saved and current_tracking_operation == TrackingOperation.ADD) or (
            is_saved and current_tracking_operation == TrackingOperation.UPDATE
        ):
            logger.debug(
                "Entity %d is already being tracking in state %s for entity type %s",
                identifier,
                current_tracking_operation,
                entity_type,
            )
            return

        if current_tracking_operation is not None:
            self.__remove_tracking_state(identifier, current_tracking_operation, entity_type)

        if is_saved:
            self.__set_tracking_state(model, identifier, TrackingOperation.UPDATE)
        else:
            self.__set_tracking_state(model, identifier, TrackingOperation.ADD)

    def __get_current_tracking_operation(
        self, identifier: int, entity_type: EntityStateType
    ) -> Optional[TrackingOperation]:
        for operation in TrackingOperation:
            if identifier in self._state[operation][entity_type]:
                return operation

        return None

    def __get_entity_saved(self, model: TrackedEntity) -> bool:
        return model.element_id is not None

    def __get_entity_identifier(self, model: TrackedEntity) -> int:
        return id(model)

    def __get_entity_type(self, model: TrackedEntity) -> EntityStateType:
        return "nodes" if isinstance(model, Node) else "relationships"

    def __set_tracking_state(
        self, model: TrackedEntity, identifier: int, tracking_operation: TrackingOperation
    ) -> None:
        logger.debug(
            "Tracking entity %d in new state %s for entity type %s",
            identifier,
            tracking_operation,
            "nodes" if isinstance(model, Node) else "relationships",
        )

        if isinstance(model, Node):
            self._state[tracking_operation]["nodes"][identifier] = (
                model,
                model._compute_checksums(),
            )
        else:
            self._state[tracking_operation]["relationships"][identifier] = (
                model,
                model._compute_checksums(),
            )

    def __remove_tracking_state(
        self, identifier: int, tracking_operation: TrackingOperation, entity_type: EntityStateType
    ) -> None:
        logger.debug(
            "Entity %d has previously tracked in state %s for entity type %s. Removing entity from tracked state",
            identifier,
            tracking_operation,
            entity_type,
        )
        removed = self._state[tracking_operation][entity_type].pop(identifier, None)

        if removed is None:  # pragma: no cover
            logger.warning(
                "Entity %d could not be removed from previously tracked state. This might indicate "
                "change tracker state inconsistencies",
                identifier,
            )

    def __set_initial_state(self) -> None:
        self._state = {
            TrackingOperation.ADD: {"nodes": {}, "relationships": {}},
            TrackingOperation.UPDATE: {"nodes": {}, "relationships": {}},
            TrackingOperation.DELETE: {"nodes": {}, "relationships": {}},
        }
        self._grouping_map = {}
