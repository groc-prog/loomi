from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    LiteralString,
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

from loomi._logger import _LogContextKey, _logger, _scoped_log_ctx
from loomi.exceptions import ChangeTrackerError, ModelError
from loomi.models.node import Node
from loomi.models.relationship import Relationship

if TYPE_CHECKING:
    from loomi.client.async_client import AsyncClient
    from loomi.client.sync_client import Client
else:
    AsyncClient = object
    Client = object

T = TypeVar(
    "T", bound=Union[neo4j.Session, neo4j.AsyncSession, neo4j.Transaction, neo4j.AsyncTransaction]
)


class _NodeInsertProperties(TypedDict):
    id_: int
    properties: Dict[str, Any]


class _NodeInsertBatch(TypedDict):
    labels: Set[str]
    batches: List[_NodeInsertProperties]


class _RelationshipInsertProperties(TypedDict):
    start_node_id: Union[str, int]
    end_node_id: Union[str, int]
    properties: Dict[str, Any]


class _RelationshipInsertBatch(TypedDict):
    type_: str
    batches: List[_RelationshipInsertProperties]


class _EntityUpdateBatch(TypedDict):
    id_: Union[str, int]
    properties: Dict[str, Any]


class _TrackingOperation(Enum):
    INSERT = 0
    DELETE = 1
    UPDATE = 2


class _TrackingOperationState(TypedDict):
    nodes: Dict[int, Tuple[Node, Dict[str, Optional[str]]]]
    relationships: Dict[int, Tuple[Relationship, Dict[str, Optional[str]]]]


class _BaseChangeTracker(Generic[T]):
    _state: Dict[_TrackingOperation, _TrackingOperationState]
    _grouping_map: Dict[int, Tuple[int, int]]
    _session_or_tx: T
    _client: Union[Client, AsyncClient]

    def __init__(self, session_or_tx: T, client: Union[Client, AsyncClient]):
        self._state = {
            _TrackingOperation.INSERT: {"nodes": {}, "relationships": {}},
            _TrackingOperation.UPDATE: {"nodes": {}, "relationships": {}},
            _TrackingOperation.DELETE: {"nodes": {}, "relationships": {}},
        }
        self._grouping_map = {}
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
        model: Union[Node, Relationship],
        start_node: Optional[Node] = None,
        end_node: Optional[Node] = None,
    ) -> None:
        """
        Starts tracking a model in the change tracker. The entity will be saved/updated once the
        change tracker is flushed.

        [!NOTE] Depending on whether the model has been `persisted or not`, any model passed to this
        function will be tracked as `UPDATE` (element_id set) or `INSERT` (element_id not set).

        Args:
            model (Union[Node, Relationship]): The model to start tracking.
            start_node (Optional[Node]): The start node of the relationship. Only relevant if
            `model` is a `Relationship`.
            end_node (Optional[Node]): The end node of the relationship. Only relevant if
            `model` is a `Relationship`.

        Raises:
            ChangeTrackerError: If start- or end nodes are missing when a relationship model is
            provided.
        """
        obj_id = id(model)
        is_relationship = isinstance(model, Relationship)
        operation = (
            _TrackingOperation.UPDATE
            if model._element_id is not None
            else _TrackingOperation.INSERT
        )

        with _scoped_log_ctx(
            {
                _LogContextKey.MODEL: model.__class__.__name__,
                _LogContextKey.MODEL_IDENTIFIER: obj_id,
                _LogContextKey.CHANGE_TRACKER_OPERATION: operation.name,
            }
        ):
            # If the entity is already being tracked with `_TrackingOperation.DELETE`, this
            # acts as a reversal, by either removing it from the tracker if it has not been
            # saved to the DB or by reversing it back to `_TrackingOperation.UPDATE`
            tracked_as_delete = self._state[_TrackingOperation.DELETE]["nodes"].get(
                obj_id
            ) or self._state[_TrackingOperation.DELETE]["relationships"].get(obj_id)
            if tracked_as_delete is not None:
                if model._element_id is not None:
                    _logger.debug(
                        "Persisted entity has previously been tracked as %s, updating to tracking "
                        "operation %s",
                        _TrackingOperation.DELETE.name,
                        _TrackingOperation.UPDATE.name,
                    )
                    if is_relationship:
                        reference = self._state[_TrackingOperation.DELETE]["relationships"].pop(
                            obj_id
                        )
                        self._state[_TrackingOperation.UPDATE]["relationships"][obj_id] = reference
                    else:
                        reference = self._state[_TrackingOperation.DELETE]["nodes"].pop(obj_id)
                        self._state[_TrackingOperation.UPDATE]["nodes"][obj_id] = reference

                    return

                if model._element_id is None:
                    _logger.debug(
                        "Non-persisted entity has previously been tracked as %s, removing entity "
                        "from tracker",
                        _TrackingOperation.DELETE.name,
                    )

                    if is_relationship:
                        reference = self._state[_TrackingOperation.DELETE]["relationships"].pop(
                            obj_id
                        )
                    else:
                        reference = self._state[_TrackingOperation.DELETE]["nodes"].pop(obj_id)

                    return

            if is_relationship and model._element_id is None:
                if start_node is None or end_node is None:
                    raise ChangeTrackerError(
                        "Both start and end nodes have to be defined when tracking a unsaved "
                        "relationship"
                    )

                start_node_id = id(start_node)
                start_node_operation = (
                    _TrackingOperation.UPDATE
                    if start_node._element_id is not None
                    else _TrackingOperation.INSERT
                )
                if start_node_id not in self._state[start_node_operation]["nodes"]:
                    self._state[start_node_operation]["nodes"][start_node_id] = (
                        start_node,
                        start_node._compute_checksums(),
                    )

                end_node_id = id(end_node)
                end_node_operation = (
                    _TrackingOperation.UPDATE
                    if end_node._element_id is not None
                    else _TrackingOperation.INSERT
                )
                if end_node_id not in self._state[end_node_operation]["nodes"]:
                    self._state[end_node_operation]["nodes"][end_node_id] = (
                        end_node,
                        end_node._compute_checksums(),
                    )

                # Remember the dependencies between relationship and nodes to be able to resolve
                # the queries later on
                self._grouping_map[obj_id] = (start_node_id, end_node_id)

            if is_relationship:
                tracked_state = self._state[operation]["relationships"].get(obj_id)
            else:
                tracked_state = self._state[operation]["nodes"].get(obj_id)

            if tracked_state is not None:
                # If the entity is already being tracked and the operation is not
                # `_TrackingOperation.REMOVE`, it is already being tracked with the correct
                # operation
                if operation != _TrackingOperation.DELETE:
                    _logger.warning(
                        "Entity has already been added to the change tracker. It will only be "
                        "tracked once"
                    )
                    return

            _logger.debug("Tracking new entity")
            if is_relationship:
                self._state[operation]["relationships"][obj_id] = (
                    model,
                    model._compute_checksums(),
                )
            else:
                self._state[operation]["nodes"][obj_id] = (model, model._compute_checksums())

    def remove(self, model: Union[Node, Relationship]) -> None:
        """
        Starts tracking a existing model to be deleted in the change tracker. The entity will be
        deleted once the change tracker is flushed.

        Args:
            model (Union[Node, Relationship]): The model to start tracking.

        Raises:
            ModelTrackingError: If a invalid model is provided.
            ChangeTrackerError: If the model has not been persisted or tracked yet.
        """
        obj_id = id(model)
        is_relationship = isinstance(model, Relationship)
        operation = (
            _TrackingOperation.UPDATE
            if model._element_id is not None
            else _TrackingOperation.INSERT
        )

        with _scoped_log_ctx(
            {
                _LogContextKey.MODEL: model.__class__.__name__,
                _LogContextKey.MODEL_IDENTIFIER: obj_id,
                _LogContextKey.CHANGE_TRACKER_OPERATION: _TrackingOperation.DELETE.name,
            }
        ):
            if is_relationship:
                tracked_state = self._state[operation]["relationships"].get(obj_id)
            else:
                tracked_state = self._state[operation]["nodes"].get(obj_id)

            if model._element_id is None:
                if tracked_state is None:
                    raise ChangeTrackerError(
                        "Can not track a entity to be deleted if it has not been persisted "
                        "to the database and has not been previously added to the change tracker"
                    )

                _logger.debug(
                    "Non persisted entity has been previously added to change tracker, stopping "
                    "tracking"
                )
                if is_relationship:
                    self._state[operation]["relationships"].pop(obj_id)
                else:
                    self._state[operation]["nodes"].pop(obj_id)

                return

            if tracked_state is not None:
                _logger.debug(
                    "Persisted entity has previously been tracked as %s, updating to tracking "
                    "operation %s",
                    operation.name,
                    _TrackingOperation.DELETE.name,
                )

                if is_relationship:
                    reference = self._state[operation]["relationships"].pop(obj_id)
                    self._state[_TrackingOperation.DELETE]["relationships"][obj_id] = reference
                else:
                    reference = self._state[operation]["nodes"].pop(obj_id)
                    self._state[_TrackingOperation.DELETE]["nodes"][obj_id] = reference

                return

            _logger.debug("Tracking new entity")
            if is_relationship:
                self._state[_TrackingOperation.DELETE]["relationships"][obj_id] = (
                    model,
                    model._compute_checksums(),
                )
            else:
                self._state[_TrackingOperation.DELETE]["nodes"][obj_id] = (
                    model,
                    model._compute_checksums(),
                )

    def clear(self) -> None:
        """
        Clears all tracked models from the change tracker. This is automatically called when
        `.flush()` is called.
        """
        _logger.debug("Clearing change tracker")
        self._state = {
            _TrackingOperation.INSERT: {"nodes": {}, "relationships": {}},
            _TrackingOperation.UPDATE: {"nodes": {}, "relationships": {}},
            _TrackingOperation.DELETE: {"nodes": {}, "relationships": {}},
        }
        self._grouping_map = {}

    def _omit_redundant_relationship_operations(self) -> None:
        _logger.debug("Omitting redundant operations for relationships")

        # Check if any of the grouped entities are no longer relevant, for example a relationship
        # was marked to be created, but the start/end node is being deleted
        for relationship_id, grouping in self._grouping_map.items():
            start_node_id, end_node_id = grouping

            start_node_not_tracked = (
                start_node_id not in self._state[_TrackingOperation.INSERT]["nodes"]
                and start_node_id not in self._state[_TrackingOperation.UPDATE]["nodes"]
            )
            end_node_not_tracked = (
                end_node_id not in self._state[_TrackingOperation.INSERT]["nodes"]
                and end_node_id not in self._state[_TrackingOperation.UPDATE]["nodes"]
            )

            if (
                start_node_not_tracked
                or end_node_not_tracked
                or start_node_id in self._state[_TrackingOperation.DELETE]["nodes"]
                or end_node_id in self._state[_TrackingOperation.DELETE]["nodes"]
            ):
                _logger.debug(
                    "Start or end node is being tracked with operation %s, relationship "
                    "operation can be skipped",
                    _TrackingOperation.DELETE.name,
                )
                self._state[_TrackingOperation.INSERT]["relationships"].pop(relationship_id, None)
                self._state[_TrackingOperation.UPDATE]["relationships"].pop(relationship_id, None)

    def _compile_node_add_operations(self) -> List[Tuple[str, Dict[str, Any]]]:
        from loomi.client._internal._base import _ServerType

        if len(self._state[_TrackingOperation.INSERT]["nodes"]) == 0:
            _logger.debug("No added nodes to compile queries for, skipping")
            return []

        groups: Dict[str, _NodeInsertBatch] = {}
        _logger.debug(
            "Compiling queries for node entities with operation type %s",
            _TrackingOperation.INSERT.name,
        )

        # Since we can not define labels with parameters, we have to build a separate query for
        # each label combination
        for obj_id, state in self._state[_TrackingOperation.INSERT]["nodes"].items():
            reference, _ = state

            if reference._hash is None:
                raise ModelError(
                    f"Hash on model {reference.__class__.__name__} is not initialized. Maybe you "
                    f"forgot to call {reference.model_rebuild.__name__}?"
                )

            if reference._hash not in groups:
                _logger.debug("Encountered new model type %s", reference._hash)
                labels = reference.loomi_config.get("labels")
                if labels is None:
                    raise ModelError(
                        f"Labels on model {reference.__class__.__name__} are not initialized. "
                        f"Maybe you forgot to call {reference.model_rebuild.__name__}?"
                    )

                groups[reference._hash] = {"labels": labels, "batches": []}

            groups[reference._hash]["batches"].append(
                {
                    "id_": obj_id,
                    "properties": reference._serialize(
                        cast(_ServerType, self._client._server_type), self._client._configuration
                    ),
                }
            )

        _logger.debug("Entity grouping done, compiling node queries and parameters")
        queries: List[Tuple[str, Dict[str, Any]]] = []
        entity_identifier = (
            "elementId(e)" if self._client._server_type == _ServerType.NEO4J else "id(e)"
        )

        for hash_, group in groups.items():
            _logger.debug("Compiling query for model %s", hash_)
            labels = ":".join(group["labels"])

            query = (
                "UNWIND $p0 AS r "
                f"CREATE (e:{labels}) "
                "SET e = r.properties "
                f"RETURN r.id_, {entity_identifier}"
            )
            queries.append((query, {"p0": group["batches"]}))

        return queries

    def _compile_relationship_add_operations(
        self, id_map: Dict[int, Union[str, int]]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        from loomi.client._internal._base import _ServerType

        if len(self._state[_TrackingOperation.INSERT]["relationships"]) == 0:
            _logger.debug("No added relationships to compile queries for, skipping")
            return []

        groups: Dict[str, _RelationshipInsertBatch] = {}
        _logger.debug(
            "Compiling queries for relationship entities with operation type %s",
            _TrackingOperation.INSERT.name,
        )

        for obj_id, state in self._state[_TrackingOperation.INSERT]["relationships"].items():
            reference, _ = state

            if reference._hash is None:
                raise ModelError(
                    f"Hash on model {reference.__class__.__name__} is not initialized. Maybe you "
                    f"forgot to call {reference.model_rebuild.__name__}?"
                )

            # Since relationships must define a start and end node when they are created, we have
            # to create them separately from the nodes so that we can reference the start and end
            # nodes with their ID's
            if reference._hash not in groups:
                _logger.debug("Encountered new model type %s", reference._hash)
                type_ = reference.loomi_config.get("type")
                if type_ is None:
                    raise ModelError(
                        f"Type on model {reference.__class__.__name__} is not initialized. Maybe "
                        f"you forgot to call {reference.model_rebuild.__name__}?"
                    )

                groups[reference._hash] = {"type_": type_, "batches": []}

            start_node_id, end_node_id = self._grouping_map[obj_id]

            # The actual entity ID can either be in the `id_map` parameter or on the referenced
            # node model
            _logger.debug("Getting database ID for start node")
            if start_node_id in id_map:
                start_node_entity_id = id_map[start_node_id]
            else:
                start_node_state = self._state[_TrackingOperation.UPDATE]["nodes"].get(
                    start_node_id
                )
                if start_node_state is None:
                    raise ChangeTrackerError(
                        "Start node for relationship not found in change tracker"
                    )

                start_node, _ = start_node_state
                start_node_entity_id = (
                    start_node._element_id
                    if cast(_ServerType, self._client._server_type) == _ServerType.NEO4J
                    else start_node.id
                )
                if start_node_entity_id is None:
                    raise ChangeTrackerError(
                        "Start node for relationship is being tracked as "
                        f"{_TrackingOperation.UPDATE.name} but is not saved to database",
                    )

            _logger.debug("Getting database ID for end node")
            if end_node_id in id_map:
                end_node_entity_id = id_map[end_node_id]
            else:
                end_node_state = self._state[_TrackingOperation.UPDATE]["nodes"].get(end_node_id)
                if end_node_state is None:
                    raise ChangeTrackerError(
                        "End node for relationship not found in change tracker"
                    )

                end_node, _ = end_node_state
                end_node_entity_id = (
                    end_node._element_id
                    if cast(_ServerType, self._client._server_type) == _ServerType.NEO4J
                    else end_node.id
                )
                if end_node_entity_id is None:
                    raise ChangeTrackerError(
                        "End node for relationship is being tracked as "
                        f"{_TrackingOperation.UPDATE.name} but is not saved to database",
                    )

            groups[reference._hash]["batches"].append(
                {
                    "start_node_id": start_node_entity_id,
                    "end_node_id": end_node_entity_id,
                    "properties": reference._serialize(
                        cast(_ServerType, self._client._server_type),
                        self._client._configuration,
                    ),
                }
            )

        _logger.debug("Entity grouping done, compiling relationship queries and parameters")
        queries: List[Tuple[str, Dict[str, Any]]] = []
        entity_identifier = "elementId" if self._client._server_type == _ServerType.NEO4J else "id"

        for hash_, group in groups.items():
            _logger.debug("Compiling query for model %s", hash_)
            query = (
                f"UNWIND $p0 AS r "
                f"MATCH (n) WHERE {entity_identifier}(n) = r.start_node_id "
                f"MATCH (m) WHERE {entity_identifier}(m) = r.end_node_id "
                f"CREATE (n)-[e:{group["type_"]}]->(m) "
                "SET e = r.properties"
            )
            queries.append((query, {"p0": group["batches"]}))

        return queries

    def _compile_node_update_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        from loomi.client._internal._base import _ServerType

        if len(self._state[_TrackingOperation.UPDATE]["nodes"]) == 0:
            _logger.debug("No updated nodes to compile queries for, skipping")
            return None

        _logger.debug("Compiling entity queries and parameters")
        node_batches: List[_EntityUpdateBatch] = []

        for state in self._state[_TrackingOperation.UPDATE]["nodes"].values():
            reference, original_checksums = state

            if reference._element_id is None or reference._id is None:
                raise ChangeTrackerError(
                    f"Entity is being tracked as {_TrackingOperation.UPDATE.name} but has not "
                    "been saved to the database yet"
                )

            updated_checksums = reference._compute_checksums()
            changed_fields = [
                field_name
                for field_name, checksum in updated_checksums.items()
                if checksum not in (original_checksums[field_name], None)
            ]

            if len(changed_fields) == 0:
                _logger.debug("Entity %s has no changes, skipping")
                continue

            _logger.debug("Found %d changed properties", len(changed_fields))
            node_batches.append(
                {
                    "id_": (
                        reference._element_id
                        if self._client._server_type == _ServerType.NEO4J
                        else reference._id
                    ),
                    "properties": reference._serialize(
                        cast(_ServerType, self._client._server_type),
                        self._client._configuration,
                        include=changed_fields,
                    ),
                }
            )

        entity_identifier = (
            "elementId(e)" if self._client._server_type == _ServerType.NEO4J else "id(e)"
        )
        node_query = (
            "UNWIND $p0 AS r "
            "MATCH (e) "
            f"WHERE {entity_identifier} = r.id_ "
            "SET e += r.properties"
        )

        return (node_query, {"p0": node_batches})

    def _compile_relationship_update_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        from loomi.client._internal._base import _ServerType

        if len(self._state[_TrackingOperation.UPDATE]["relationships"]) == 0:
            _logger.debug("No updated relationships to compile queries for, skipping")
            return None

        _logger.debug("Compiling entity queries and parameters")
        relationship_batches: List[_EntityUpdateBatch] = []

        for state in self._state[_TrackingOperation.UPDATE]["relationships"].values():
            reference, original_checksums = state

            if reference._element_id is None or reference._id is None:
                raise ChangeTrackerError(
                    f"Entity is being tracked as {_TrackingOperation.UPDATE.name} but has not "
                    "been saved to the database yet"
                )

            updated_checksums = reference._compute_checksums()
            changed_fields = [
                field_name
                for field_name, checksum in updated_checksums.items()
                if checksum not in (original_checksums[field_name], None)
            ]

            if len(changed_fields) == 0:
                _logger.debug("Entity %s has no changes, skipping")
                continue

            _logger.debug("Found %d changed properties", len(changed_fields))
            relationship_batches.append(
                {
                    "id_": (
                        reference._element_id
                        if self._client._server_type == _ServerType.NEO4J
                        else reference._id
                    ),
                    "properties": reference._serialize(
                        cast(_ServerType, self._client._server_type),
                        self._client._configuration,
                        include=changed_fields,
                    ),
                }
            )

        entity_identifier = (
            "elementId(e)" if self._client._server_type == _ServerType.NEO4J else "id(e)"
        )
        relationship_query = (
            "UNWIND $p0 AS r "
            "MATCH ()-[e]->() "
            f"WHERE {entity_identifier} = r.id_ "
            "SET e += r.properties"
        )

        return (relationship_query, {"p0": relationship_batches})

    def _compile_node_delete_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        from loomi.client._internal._base import _ServerType

        if len(self._state[_TrackingOperation.DELETE]["nodes"]) == 0:
            _logger.debug("No deleted nodes to compile queries for, skipping")
            return None

        _logger.debug("Compiling entity queries and parameters")
        node_ids: List[Union[str, int]] = []

        for state in self._state[_TrackingOperation.DELETE]["nodes"].values():
            reference, _ = state

            if reference._element_id is None or reference._id is None:
                raise ChangeTrackerError(
                    f"Entity is being tracked as {_TrackingOperation.DELETE.name} but has not "
                    "been saved to the database yet"
                )

            node_ids.append(
                reference._element_id
                if self._client._server_type == _ServerType.NEO4J
                else reference._id
            )

        entity_identifier = (
            "elementId(e)" if self._client._server_type == _ServerType.NEO4J else "id(e)"
        )
        node_query = f"UNWIND $p0 AS r MATCH (e) WHERE {entity_identifier} = r DETACH DELETE e"

        return (node_query, {"p0": node_ids})

    def _compile_relationship_delete_operations(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        from loomi.client._internal._base import _ServerType

        if len(self._state[_TrackingOperation.DELETE]["relationships"]) == 0:
            _logger.debug("No deleted relationships to compile queries for, skipping")
            return None

        _logger.debug("Compiling entity queries and parameters")
        relationship_ids: List[Union[str, int]] = []

        for state in self._state[_TrackingOperation.DELETE]["relationships"].values():
            reference, _ = state

            if reference._element_id is None or reference._id is None:
                raise ChangeTrackerError(
                    f"Entity is being tracked as {_TrackingOperation.DELETE.name} but has not "
                    "been saved to the database yet"
                )

            relationship_ids.append(
                reference._element_id
                if self._client._server_type == _ServerType.NEO4J
                else reference._id
            )

        entity_identifier = (
            "elementId(e)" if self._client._server_type == _ServerType.NEO4J else "id(e)"
        )
        relationship_query = (
            f"UNWIND $p0 AS r MATCH ()-[e]->() WHERE {entity_identifier} = r DELETE e"
        )

        return (relationship_query, {"p0": relationship_ids})


class ChangeTracker(_BaseChangeTracker[Union[neo4j.Session, neo4j.Transaction]]):
    """Manages state synchronization between local entities and the database state."""

    def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `Session`, a `new transaction` will be created (based on
        the current session) which will run all queries and `commit them`. If this is called
        on a `Transaction`, the flushed queries will be `part of that transaction` and
        will only be committed once `tx.commit()` is called.
        """
        with _scoped_log_ctx(
            {
                _LogContextKey.DRIVER: self._client.__class__.__name__,
                _LogContextKey.SERVER_TYPE: self._client._server_type,
            }
        ):
            self._omit_redundant_relationship_operations()

            if isinstance(self._session_or_tx, neo4j.Session):
                # If the change tracker is called on a session, we create a new transaction and run
                # every operation in that transaction
                self._flush_with_session()
            else:
                # If this is called on a transaction already, we pass the responsibility of calling
                # `.commit()` to the caller
                self._flush_with_transaction()

            self.clear()

    def _flush_with_session(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        _logger.debug("Flush called on session, creating new transaction to run pending changes")

        with cast(neo4j.Session, self._session_or_tx).begin_transaction() as tx:
            for query, parameters in self._compile_node_add_operations():
                result = tx.run(cast(LiteralString, query), parameters)

                entity_id_map = cast(Dict[int, Union[str, int]], dict(result.values()))
                id_map.update(entity_id_map)

            queries = [*self._compile_relationship_add_operations(id_map)]

            node_update_queries = self._compile_node_update_operations()
            if node_update_queries is not None:
                queries.append(node_update_queries)

            relationship_update_queries = self._compile_relationship_update_operations()
            if relationship_update_queries is not None:
                queries.append(relationship_update_queries)

            node_delete_queries = self._compile_node_delete_operations()
            if node_delete_queries is not None:
                queries.append(node_delete_queries)

            relationship_delete_queries = self._compile_relationship_delete_operations()
            if relationship_delete_queries is not None:
                queries.append(relationship_delete_queries)

            for query_info in queries:
                query, parameters = query_info
                result = tx.run(cast(LiteralString, query), parameters)
                result.consume()

    def _flush_with_transaction(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        _logger.debug(
            "Flush called on transaction, run pending changes directly on transaction "
            "without committing changes"
        )
        for query, parameters in self._compile_node_add_operations():
            result = self._session_or_tx.run(cast(LiteralString, query), parameters)

            entity_id_map = cast(Dict[int, Union[str, int]], dict(result.values()))
            id_map.update(entity_id_map)

        queries = [*self._compile_relationship_add_operations(id_map)]

        node_update_queries = self._compile_node_update_operations()
        if node_update_queries is not None:
            queries.append(node_update_queries)

        relationship_update_queries = self._compile_relationship_update_operations()
        if relationship_update_queries is not None:
            queries.append(relationship_update_queries)

        node_delete_queries = self._compile_node_delete_operations()
        if node_delete_queries is not None:
            queries.append(node_delete_queries)

        relationship_delete_queries = self._compile_relationship_delete_operations()
        if relationship_delete_queries is not None:
            queries.append(relationship_delete_queries)

        for query_info in queries:
            query, parameters = query_info
            result = self._session_or_tx.run(cast(LiteralString, query), parameters)
            result.consume()


class AsyncChangeTracker(_BaseChangeTracker[Union[neo4j.AsyncSession, neo4j.AsyncTransaction]]):
    """Manages state synchronization between local entities and the database state."""

    async def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `AsyncSession`, a `new transaction` will be created (based
        on the current session) which will run all queries and `commit them`. If this is called
        on a `AsyncTransaction`, the flushed queries will be `part of that transaction` and
        will only be committed once `tx.commit()` is called.
        """
        with _scoped_log_ctx(
            {
                _LogContextKey.DRIVER: self._client.__class__.__name__,
                _LogContextKey.SERVER_TYPE: self._client._server_type,
            }
        ):
            self._omit_redundant_relationship_operations()

            if isinstance(self._session_or_tx, neo4j.AsyncSession):
                # If the change tracker is called on a session, we create a new transaction and run
                # every operation in that transaction
                await self._flush_with_session()
            else:
                # If this is called on a transaction already, we pass the responsibility of calling
                # `.commit()` to the caller
                await self._flush_with_transactions()

        self.clear()

    async def _flush_with_session(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        _logger.debug("Flush called on session, creating new transaction to run pending changes")

        async with await cast(neo4j.AsyncSession, self._session_or_tx).begin_transaction() as tx:
            for query, parameters in self._compile_node_add_operations():
                result = await tx.run(cast(LiteralString, query), parameters)

                entity_id_map = cast(Dict[int, Union[str, int]], dict(await result.values()))
                id_map.update(entity_id_map)

            queries = [*self._compile_relationship_add_operations(id_map)]

            node_update_queries = self._compile_node_update_operations()
            if node_update_queries is not None:
                queries.append(node_update_queries)

            relationship_update_queries = self._compile_relationship_update_operations()
            if relationship_update_queries is not None:
                queries.append(relationship_update_queries)

            node_delete_queries = self._compile_node_delete_operations()
            if node_delete_queries is not None:
                queries.append(node_delete_queries)

            relationship_delete_queries = self._compile_relationship_delete_operations()
            if relationship_delete_queries is not None:
                queries.append(relationship_delete_queries)

            for query_info in queries:
                query, parameters = query_info
                result = await tx.run(cast(LiteralString, query), parameters)
                await result.consume()

    async def _flush_with_transactions(self) -> None:
        id_map: Dict[int, Union[str, int]] = {}
        _logger.debug(
            "Flush called on transaction, run pending changes directly on transaction without "
            "committing changes"
        )
        for query, parameters in self._compile_node_add_operations():
            result = await self._session_or_tx.run(cast(LiteralString, query), parameters)

            entity_id_map = cast(Dict[int, Union[str, int]], dict(await result.values()))
            id_map.update(entity_id_map)

        queries = [*self._compile_relationship_add_operations(id_map)]

        node_update_queries = self._compile_node_update_operations()
        if node_update_queries is not None:
            queries.append(node_update_queries)

        relationship_update_queries = self._compile_relationship_update_operations()
        if relationship_update_queries is not None:
            queries.append(relationship_update_queries)

        node_delete_queries = self._compile_node_delete_operations()
        if node_delete_queries is not None:
            queries.append(node_delete_queries)

        relationship_delete_queries = self._compile_relationship_delete_operations()
        if relationship_delete_queries is not None:
            queries.append(relationship_delete_queries)

        for query_info in queries:
            query, parameters = query_info
            result = await self._session_or_tx.run(cast(LiteralString, query), parameters)
            await result.consume()
