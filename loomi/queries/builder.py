from typing import Protocol

from loomi.queries._internal._mixins import _HasMatch, _HasSet
from loomi.queries._internal._state import _InternalBuilderState


class _StateProtocol(Protocol):
    _state: _InternalBuilderState


class LoomiQuery(_HasMatch):
    def __init__(self):
        super().__init__()
        self._state = _InternalBuilderState()


class _QueryState(_HasMatch):
    def __init__(self, state: _InternalBuilderState):
        super().__init__()
        self._state = state


class _MatchState(_QueryState, _HasMatch, _HasSet): ...


class _SetState(_QueryState, _HasSet): ...
