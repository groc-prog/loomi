from dataclasses import dataclass
from enum import Enum
from typing import Dict, Generic, Optional, TypedDict, TypeVar, Union, overload

from neo4j import AsyncSession, AsyncTransaction, Session, Transaction

from loomi._logger import _LogContextKey, _logger, _scoped_log_ctx
from loomi.client._internal.session import LoomiAsyncSession, LoomiSession
from loomi.exceptions import ModelTrackingError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

T = TypeVar("T", bound=Union[Session, AsyncSession, Transaction, AsyncTransaction])


class _State(TypedDict):
    nodes: Dict[int, "_TrackingInfo"]
    relationships: Dict[int, "_TrackingInfo"]


class _TrackingOperation(Enum):
    ADD = 0
    REMOVE = 1
    UPDATE = 2


@dataclass
class _TrackingInfo:
    reference: Union[LoomiNode, LoomiRelationship]
    operation: _TrackingOperation
    start_node_id: Optional[int] = None
    end_node_id: Optional[int] = None


class _BaseChangeTracker(Generic[T]):
    _state: _State
    _session_or_tx: T

    def __init__(self, session_or_tx: T):
        self._state = {"nodes": {}, "relationships": {}}
        self._session_or_tx = session_or_tx

    @overload
    def add(self, model: LoomiNode) -> None: ...

    @overload
    def add(
        self,
        model: LoomiRelationship,
        start_node: Optional[LoomiNode] = None,
        end_node: Optional[LoomiNode] = None,
    ) -> None: ...

    def add(
        self,
        model: Union[LoomiNode, LoomiRelationship],
        start_node: Optional[LoomiNode] = None,
        end_node: Optional[LoomiNode] = None,
    ) -> None:
        """
        Starts tracking a model in the change tracker. The entity will be saved/updated once the
        change tracker is flushed.

        Args:
            model (Union[LoomiNode, LoomiRelationship]): The model to start tracking.
            start_node (Optional[LoomiNode]): The start node of the relationship. Only relevant if
            `model` is a `LoomiRelationship`.
            end_node (Optional[LoomiNode]): The end node of the relationship. Only relevant if
            `model` is a `LoomiRelationship`.
        """
        obj_id = id(model)
        is_relationship = isinstance(model, LoomiRelationship)
        state_type = "relationships" if is_relationship else "nodes"
        operation = (
            _TrackingOperation.UPDATE if model.element_id is not None else _TrackingOperation.ADD
        )

        with _scoped_log_ctx(
            {
                _LogContextKey.MODEL: model.__class__.__name__,
                _LogContextKey.MODEL_IDENTIFIER: obj_id,
                _LogContextKey.CHANGE_TRACKER_OPERATION: operation.name,
            }
        ):
            if is_relationship and model.element_id is None:
                if start_node is None or end_node is None:
                    raise ModelTrackingError(
                        "Both start and end nodes have to be defined when tracking a unsaved "
                        "relationship"
                    )

                start_node_id = id(start_node)
                if start_node_id not in self._state["nodes"]:
                    self._state["nodes"][start_node_id] = _TrackingInfo(
                        start_node,
                        (
                            _TrackingOperation.UPDATE
                            if start_node.element_id is not None
                            else _TrackingOperation.ADD
                        ),
                    )

                end_node_id = id(end_node)
                if end_node_id not in self._state["nodes"]:
                    self._state["nodes"][end_node_id] = _TrackingInfo(
                        end_node,
                        (
                            _TrackingOperation.UPDATE
                            if end_node.element_id is not None
                            else _TrackingOperation.ADD
                        ),
                    )

            tracked_state = self._state.get(state_type, {}).get(obj_id)

            # If the entity is already being tracked and the operation is not
            # `_TrackingOperation.REMOVE`, it is already being tracked with the correct operation
            if tracked_state is not None and tracked_state.operation != _TrackingOperation.REMOVE:
                _logger.warning(
                    "Entity has already been added to the change tracker. It will only be tracked "
                    "once"
                )
                return

            # If the entity has been persisted to the DB and tracked_state is not None at this
            # point, it has previously been added with a `_TrackingOperation.REMOVE`
            # This acts like a reversal, so we reset the operation type to
            # `_TrackingOperation.UPDATE`
            if model.element_id is not None and tracked_state is not None:
                _logger.debug(
                    "Persisted entity has previously been tracked as %s, updating to tracking "
                    "operation %s",
                    _TrackingOperation.REMOVE.name,
                    _TrackingOperation.UPDATE.name,
                )
                self._state[state_type][obj_id].operation = _TrackingOperation.UPDATE
                return

            # At this point we have a non persisted model which has been marked for deletion
            # This again acts as a reversal, so we can set the operation back to
            # `_TrackingOperation.ADD`
            if model.element_id is None and tracked_state is not None:
                _logger.debug(
                    "Non-persisted entity has previously been tracked as %s, updating to tracking "
                    "operation %s",
                    _TrackingOperation.REMOVE.name,
                    _TrackingOperation.ADD.name,
                )
                self._state[state_type][obj_id].operation = _TrackingOperation.ADD
                return

            _logger.debug("Tracking new entity")
            self._state[state_type][obj_id] = _TrackingInfo(
                model,
                operation,
                id(start_node) if is_relationship else None,
                id(end_node) if is_relationship else None,
            )

    def remove(self, model: Union[LoomiNode, LoomiRelationship]) -> None:
        """
        Starts tracking a existing model to be deleted in the change tracker. The entity will be
        deleted once the change tracker is flushed.

        Args:
            model (Union[LoomiNode, LoomiRelationship]): The model to start tracking.

        Raises:
            ModelTrackingError: If a invalid model is provided.
        """
        obj_id = id(model)
        is_relationship = isinstance(model, LoomiRelationship)
        state_type = "relationships" if is_relationship else "nodes"

        with _scoped_log_ctx(
            {
                _LogContextKey.MODEL: model.__class__.__name__,
                _LogContextKey.MODEL_IDENTIFIER: obj_id,
                _LogContextKey.CHANGE_TRACKER_OPERATION: _TrackingOperation.REMOVE.name,
            }
        ):
            # If the node is already referenced by some other relationship, we can not mark
            # it to be deleted, as the relationship operation will fail otherwise
            if not is_relationship:
                _logger.debug("Checking if node entity is referenced by a relationship")
                is_referenced = any(
                    relationship_state
                    for relationship_state in self._state["relationships"].values()
                    if relationship_state.start_node_id == obj_id
                    or relationship_state.end_node_id == obj_id
                )

                if is_referenced:
                    raise ModelTrackingError(
                        "Entity can not be tracked as deleted since it is referenced by one or "
                        "more relationship entities"
                    )

            tracked_state = self._state.get(state_type, {}).get(obj_id)
            if model.element_id is None:
                if tracked_state is None:
                    raise ModelTrackingError(
                        "Can not track a entity to be deleted if it has not been persisted "
                        "to the database and has not been previously added to the change tracker"
                    )

                _logger.debug(
                    "Non persisted entity has been previously added to change tracker, stopping "
                    "tracking"
                )
                self._state[state_type].pop(obj_id)
                return

            if tracked_state is not None:
                _logger.debug(
                    "Persisted entity has previously been tracked as %s, updating to tracking "
                    "operation %s",
                    tracked_state.operation.name,
                    _TrackingOperation.UPDATE.name,
                )
                self._state[state_type][obj_id].operation = _TrackingOperation.REMOVE
                return

            _logger.debug("Tracking new entity")
            self._state[state_type][obj_id] = _TrackingInfo(
                model,
                _TrackingOperation.REMOVE,
            )

    def clear(self) -> None:
        """
        Clears all tracked models from the change tracker. This is automatically called when
        `.flush()` is called.
        """
        _logger.debug("Clearing change tracker")
        self._state = {"nodes": {}, "relationships": {}}


class _ChangeTracker(_BaseChangeTracker[Union[Session, Transaction]]):
    def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `LoomiSession`, a `new transaction` will be created (based on
        the current session) which will run all queries and `commit them`. If this is called
        on a `LoomiTransaction`, the flushed queries will be `part of that transaction` and
        will only be committed once `tx.commit()` is called.
        """

        if isinstance(self._session_or_tx, LoomiSession):
            with self._session_or_tx.begin_transaction() as tx:
                # TODO: Run all queries from change tracker here
                tx.commit()
        else:
            # TODO: Run all queries from change tracker here, but do not commit
            ...


class _AsyncChangeTracker(_BaseChangeTracker[Union[AsyncSession, AsyncTransaction]]):
    async def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `LoomiAsyncSession`, a `new transaction` will be created (based
        on the current session) which will run all queries and `commit them`. If this is called
        on a `LoomiAsyncTransaction`, the flushed queries will be `part of that transaction` and
        will only be committed once `tx.commit()` is called.
        """

        if isinstance(self._session_or_tx, LoomiAsyncSession):
            async with await self._session_or_tx.begin_transaction() as tx:
                # TODO: Run all queries from change tracker here
                await tx.commit()
        else:
            # TODO: Run all queries from change tracker here, but do not commit
            ...
