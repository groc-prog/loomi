from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, Union, overload

from loomi.constants._graph import _ModelType
from loomi.exceptions import QueryCompileError
from loomi.models._base import _PropertyAccessor
from loomi.query._builder import CompiledLoomiQuery
from loomi.query.helpers import _Predicate, _PredicateGroup

if TYPE_CHECKING:
    from loomi.query._state import (
        _InternalQueryState,
        _MatchQueryState,
        _SetQueryState,
        _WhereQueryState,
    )
else:
    _InternalQueryState = object
    _MatchQueryState = object
    _SetQueryState = object
    _WhereQueryState = object


class _HasState(Protocol):
    _state: _InternalQueryState


class _CanMatch(_HasState):
    def match(self, model: _ModelType, alias: Optional[str] = None) -> "_MatchQueryState":
        """
        Adds a new `MATCH` pattern to the query. If more than one `MATCH` pattern is added, a
        `alias should be used` to control separate patterns.

        Args:
            model (Union[Type[LoomiNode], Type[LoomiRelationship]]): The model to compile a
            pattern for.
            alias (Optional[str]): A optional alias for the pattern to reference it later.
            Defaults to `None`.
        """
        from loomi.query._state import _MatchQueryState

        self._state.add_match_pattern(model, alias)
        return _MatchQueryState(self._state)


class _CanSet(_HasState):
    @overload
    def set(self, properties: Dict[str, Any], alias: Optional[str] = None) -> _SetQueryState: ...

    @overload
    def set(self, accessor: Any, value: Any, alias: Optional[str] = None) -> _SetQueryState: ...

    def set(  # type: ignore
        self, arg1: Any, arg2: Any, arg3: Optional[str] = None
    ) -> _SetQueryState:
        """
        Adds a new `SET` clause to the query.

        [!NOTE] If more than one `MATCH` pattern was already added, a `alias must be used` to
        define which pattern the WHERE clause should affect.

        Args:
            arg1 (Union[_QueryAccessor, str, dict[str, Any]]): Either a accessor, a dictionary
            containing multiple properties or a alias.
            arg2 (Optional[Union[Any, _QueryAccessor, dict[str, Any]]]): Either a accessor, a
            dictionary containing multiple properties or the value to set.
            arg3 (Optional[Any]): The value to set.
        """
        # Dictionary with multiple accessors/keys has been defined
        if isinstance(arg1, dict):
            alias = arg2 if isinstance(arg2, str) else None

            for (
                property_or_accessor,
                value,
            ) in arg1.items():
                property_name = (
                    property_or_accessor._full_path
                    if isinstance(property_or_accessor, _PropertyAccessor)
                    else str(property_or_accessor)
                )
                self._state.add_set_clause(property_name, value, alias)
        # Single accessor has been defined (e.g. `.set(Model.field, value)`)
        elif isinstance(arg1, _PropertyAccessor):
            self._state.add_set_clause(
                arg1._full_path,
                arg2,
                arg3,
            )

        raise QueryCompileError(
            (f"Invalid argument provided. Expected query accessor or properties got {arg1}")
        )


class _CanWhere(_HasState):
    def where(self, predicate_or_group: Union[_Predicate, _PredicateGroup]) -> _WhereQueryState:
        """
        Adds a new `WHERE` clause to the query.

        [!NOTE] If more than one `MATCH` pattern was already added, a `alias must be used` to
        define which pattern the WHERE clause should affect.

        Args:
            predicate_or_group (Union[_Predicate, _PredicateGroup]): The predicate or predicate
            group.
        """
        from loomi.query._state import _WhereQueryState

        self._state.add_where_clause(predicate_or_group)
        return _WhereQueryState(self._state)


class _CanReturn(_HasState):
    def returning(self, projection: Optional[Dict[str, Any]] = None) -> CompiledLoomiQuery:
        """
        Adds a final `RETURN` clause to the query. Will return all matched entities by default.

        [!NOTE] If more than one `MATCH` pattern was already added, a `alias must be used` to
        define which variables/properties should be included in the RETURN clause.

        Args:
            projection (Optional[Dict[str, Any]]): A projection defining which variables/properties
            are returned.

        Returns:
            CompiledLoomiQuery: The compiled query and it's parameters.
        """
        if projection is None:
            self._state.add_default_return_clauses()

        return self._state.compile()
