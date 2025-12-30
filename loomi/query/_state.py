from loomi.query._builder import _InternalQueryState
from loomi.query._mixin import _CanMatch, _CanReturn, _CanSet, _CanWhere


class _QueryBase:
    _state: _InternalQueryState

    def __init__(self, state: _InternalQueryState):
        self._state = state


class LoomiQuery(_QueryBase, _CanMatch):
    """Fluent interface query builder class for Loomi drivers."""

    def __init__(self):
        super().__init__(_InternalQueryState())


class _MatchQueryState(_QueryBase, _CanWhere, _CanMatch, _CanSet, _CanReturn): ...


class _SetQueryState(_QueryBase, _CanSet, _CanReturn): ...


class _WhereQueryState(_QueryBase, _CanSet, _CanReturn): ...
