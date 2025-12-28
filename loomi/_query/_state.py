from loomi._query._internal_state import _InternalQueryState
from loomi._query._mixin import _CanMatch, _CanReturn, _CanSet


class _QueryBase:
    _state: _InternalQueryState

    def __init__(self, state: _InternalQueryState):
        self._state = state


class _StartQueryState(_QueryBase, _CanMatch): ...


class _MatchQueryState(_QueryBase, _CanMatch, _CanSet, _CanReturn): ...


class _SetQueryState(_QueryBase, _CanSet, _CanReturn): ...
