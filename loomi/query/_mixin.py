from typing import TYPE_CHECKING, Any, Optional, Protocol, Union, overload

from loomi.constants._graph import _ModelType
from loomi.exceptions import QueryCompileError
from loomi.models._base import _QueryAccessor
from loomi.query.filters import _Predicate, _PredicateGroup

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
    def match(
        self, model: _ModelType, alias: Optional[str] = None
    ) -> "_MatchQueryState":
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
    def set(self, alias: str, accessor: Any, value: Any) -> _SetQueryState: ...

    @overload
    def set(self, alias: str, properties: dict[Any, Any]) -> _SetQueryState: ...

    @overload
    def set(self, accessor: Any, value: Any) -> _SetQueryState: ...

    @overload
    def set(self, properties: dict[Any, Any]) -> _SetQueryState: ...

    def set(  # type: ignore
        self,
        arg1: Union[Any, str, dict[Any, Any]],
        arg2: Optional[Union[Any, dict[Any, Any]]] = None,
        arg3: Optional[Any] = None,
    ) -> _SetQueryState:
        """
        Adds a new `SET` clause to the query. If more than one `MATCH` pattern was already added,
        a `alias must be used` to define which pattern the SET clause should affect.

        Example:
            With a query accessor:
            ```python
            class Human(LoomiNode):
                age: int

            query.set(Human.age, 24)
            ```

            With a dictionary containing either a accessor or a field name as the key:
            ```python
            class Human(LoomiNode):
                age: int
                name: str

            query.set({Human.age, 24, "name": "John"})
            ```

        Args:
            arg1 (Union[_QueryAccessor, str, dict[str, Any]]): Either a accessor, a dictionary
            containing multiple properties or a alias.
            arg2 (Optional[Union[Any, _QueryAccessor, dict[str, Any]]]): Either a accessor, a
            dictionary containing multiple properties or the value to set.
            arg3 (Optional[Any]): The value to set.
        """
        from loomi.query._state import _SetQueryState

        # Set clause with alias
        if isinstance(arg1, str):
            # Single accessor has been defined (e.g. `.set(Model.field, value)`)
            if isinstance(arg2, _QueryAccessor):
                self._state.add_set_clause(
                    arg2.name,
                    arg3,
                    arg1,
                )
            # Dictionary with multiple accessors/keys has been defined
            # (e.g. `.set({Model.field: value, "field": value})`)
            elif isinstance(arg2, dict):
                for (
                    property_or_accessor,
                    value,
                ) in arg2.items():
                    property_name = (
                        property_or_accessor.name
                        if isinstance(property_or_accessor, _QueryAccessor)
                        else str(property_or_accessor)
                    )
                    self._state.add_set_clause(property_name, value, arg1)

            return _SetQueryState(self._state)
        # Single accessor has been defined (e.g. `.set(Model.field, value)`)
        if isinstance(arg1, _QueryAccessor):
            self._state.add_set_clause(
                arg1.name,
                arg2,
                None,
            )

            return _SetQueryState(self._state)
        # Dictionary with multiple accessors/keys has been defined
        # (e.g. `.set({Model.field: value, "field": value})`)
        if isinstance(arg1, dict):
            for property_or_accessor, arg3 in arg1.items():
                property_name = (
                    property_or_accessor.name
                    if isinstance(property_or_accessor, _QueryAccessor)
                    else str(property_or_accessor)
                )
                self._state.add_set_clause(property_name, arg3, None)

            return _SetQueryState(self._state)

        raise QueryCompileError(
            (
                "Invalid argument provided. Expected query accessor, alias or properties "
                f"provided, got {arg1}"
            )
        )


class _CanWhere(_HasState):
    def where(
        self, predicate_or_group: Union[_Predicate, _PredicateGroup]
    ) -> _WhereQueryState:
        """
        Adds a new `WHERE` clause to the query. If more than one `MATCH` pattern was already added,
        a `alias must be used` to define which pattern the WHERE clause should affect.

        Example:
            With a query accessor:
            ```python
            class Human(LoomiNode):
                name: str
                age: int

            query.where(and_(eq(Human.name, "John"), gt(Human.age, 24)))
            ```

            With a property name:
            ```python
            class Human(LoomiNode):
                name: str
                age: int

            query.where(and_(eq("name", John"), gt("age", 24)))
            ```

        Args:
            predicate_or_group (Union[_Predicate, _PredicateGroup]): The predicate or predicate
            group.
        """
        from loomi.query._state import _WhereQueryState

        self._state.add_where_clause(predicate_or_group)
        return _WhereQueryState(self._state)


class _CanReturn(_HasState):
    def returning(self) -> None:
        self._state.compile_and_run()
