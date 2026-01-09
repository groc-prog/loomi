from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, OrderedDict, TypeVar, Union

from neo4j import AsyncSession, AsyncTransaction, Session, Transaction

from loomi._logger import _LogContextKey, _logger, _scoped_log_ctx
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

T = TypeVar("T", bound=Union[Session, AsyncSession, Transaction, AsyncTransaction])


class _TrackingOperation(Enum):
    ADD = 0
    REMOVE = 1
    UPDATE = 2


@dataclass
class _TrackingInfo:
    reference: Union[LoomiNode, LoomiRelationship]
    operation: _TrackingOperation
    state: Optional[Dict[str, Any]]


class _BaseChangeTracker(Generic[T]):
    _state: OrderedDict[int, _TrackingInfo]
    _session_or_tx: T

    def __init__(self, session_or_tx: T):
        self._state = OrderedDict()
        self._session_or_tx = session_or_tx

    def add(self, model: Union[LoomiNode, LoomiRelationship]) -> None:
        """
        Starts tracking a new (unsaved) model in the change tracker. The entity will be saved once
        the change tracker is flushed.

        Args:
            model (Union[LoomiNode, LoomiRelationship]): The model to start tracking.
        """
        operation_type = (
            _TrackingOperation.ADD if model.element_id is None else _TrackingOperation.UPDATE
        )
        obj_id = id(model)

        with _scoped_log_ctx(
            {
                _LogContextKey.MODEL: str(model),
                _LogContextKey.CHANGE_TRACKER_OPERATION: operation_type.name,
            }
        ):
            tracked_state = self._state.get(obj_id)
            if tracked_state is not None and tracked_state.operation == operation_type:
                _logger.debug(
                    "Entity is already being tracked with operation %s, nothing to do",
                    operation_type.name,
                )
                return

            _logger.debug("Tracking new entity")
            self._state[obj_id] = _TrackingInfo(
                model, operation_type, model.model_dump(by_alias=True)
            )

    def remove(self, model: Union[LoomiNode, LoomiRelationship]) -> None:
        """
        Starts tracking a existing model to be deleted in the change tracker. The entity will be
        deleted once the change tracker is flushed.

        Args:
            model (Union[LoomiNode, LoomiRelationship]): The model to start tracking.
        """
        obj_id = id(model)

        with _scoped_log_ctx(
            {
                _LogContextKey.MODEL: str(model),
                _LogContextKey.CHANGE_TRACKER_OPERATION: _TrackingOperation.REMOVE.name,
            }
        ):
            tracked_state = self._state.get(obj_id)
            if tracked_state is not None:
                if tracked_state.operation == _TrackingOperation.REMOVE:
                    _logger.debug(
                        "Entity is already being tracked with operation %s, nothing to do",
                        _TrackingOperation.REMOVE.name,
                    )
                    return
                if tracked_state.operation == _TrackingOperation.ADD:
                    _logger.debug(
                        "Entity is already being tracked with operation %s, removing from change "
                        "tracker",
                        _TrackingOperation.ADD.name,
                    )
                    self._state.pop(obj_id)
                    return

            _logger.debug("Tracking new entity")
            self._state[obj_id] = _TrackingInfo(model, _TrackingOperation.REMOVE, None)

    def clear(self) -> None:
        """
        Clears all tracked models from the change tracker. This is automatically called when
        `.flush()` is called.
        """
        _logger.debug("Clearing change tracker")
        self._state = OrderedDict()

    @abstractmethod
    def flush(self) -> None:
        """
        Flushes the tracker by generating and running all queries for the tracked models.

        If this is called on a `LoomiSession` or `LoomiAsyncSession`, a `new transaction` will be
        created (based on the current session) which will run all queries and `commit them`. If
        this is called on a `LoomiTransaction` or `LoomiAsyncTransaction`, the flushed queries will
        be `part of that transaction` and will only be committed once `tx.commit()` is called.
        """


class _ChangeTracker(_BaseChangeTracker[Union[Session, Transaction]]):
    def flush(self) -> None:
        queries: List[str] = []
        parameters: Dict[str, Any] = {}

        for tracked_model in self._state.values():
            pass
