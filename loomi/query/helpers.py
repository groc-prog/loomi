from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from loomi.models._base import _PropertyAccessor


@dataclass
class _Predicate:
    predicate_type: str
    """Corresponds to the name of the helper function which generated the predicate."""
    path: str
    values: Tuple[Any, ...]
    alias: Optional[str]
    template_func: Callable[[Dict[str, Any]], str]


@dataclass
class _PredicateGroup:
    group_type: str
    """Corresponds to the name of the helper function which generated the predicate group."""
    predicates: List[Union[_Predicate, "_PredicateGroup"]]
    template_func: Callable[[Dict[str, Any]], str]


def eq(accessor_or_path: Union[str, Any], value: Any, alias: Optional[str] = None) -> _Predicate:
    """
    Predicate helper function for filtering entities where a property is equal to `value`.

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (Any): The value used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        eq.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"{ctx["path"]} = ${ctx["p0"]}",
    )


def neq(accessor_or_path: Union[str, Any], value: Any, alias: Optional[str] = None) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is not equal to `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(neq(Human.age, 24))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(neq("age", 24))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (Any): The value used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        neq.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"{ctx["path"]} <> ${ctx["p0"]}",
    )


def gt(
    accessor_or_path: Union[str, Any],
    number: Union[int, float],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is greater than `number`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(gt(Human.age, 24))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(gt("age", 24))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        number (Union[int, float]): The number used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        gt.__name__,
        path,
        (number,),
        alias,
        lambda ctx: f"{ctx["path"]} > ${ctx["p0"]}",
    )


def gte(
    accessor_or_path: Union[str, Any],
    number: Union[int, float],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is greater than or equal to `number`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(gte(Human.age, 24))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(gte("age", 24))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        number (Union[int, float]): The number used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        gte.__name__,
        path,
        (number,),
        alias,
        lambda ctx: f"{ctx["path"]} >= ${ctx["p0"]}",
    )


def lt(
    accessor_or_path: Union[str, Any],
    number: Union[int, float],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is less than `number`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(lt(Human.age, 24))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(lt("age", 24))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        number (Union[int, float]): The number used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        lt.__name__,
        path,
        (number,),
        alias,
        lambda ctx: f"{ctx["path"]} < ${ctx["p0"]}",
    )


def lte(
    accessor_or_path: Union[str, Any],
    number: Union[int, float],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is less than or equal to `number`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(lte(Human.age, 24))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(lte("age", 24))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        number (Union[int, float]): The number used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        lte.__name__,
        path,
        (number,),
        alias,
        lambda ctx: f"{ctx["path"]} <= ${ctx["p0"]}",
    )


def between(
    accessor_or_path: Union[str, Any],
    min_number: Union[int, float],
    max_number: Union[int, float],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is between `min_number` and
    `max_number`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(between(Human.age, 24, 35))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(between("age", 24, 35))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        min_number (Union[int, float]): The min number used in the predicate.
        max_number (Union[int, float]): The max number used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        between.__name__,
        path,
        (min_number, max_number),
        alias,
        lambda ctx: (f"({ctx["path"]} > ${ctx["p0"]} AND {ctx["path"]} < ${ctx["p1"]})"),
    )


def not_between(
    accessor_or_path: Union[str, Any],
    min_number: Union[int, float],
    max_number: Union[int, float],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is not between `min_number` and
    `max_number`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(not_between(Human.age, 24, 35))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(not_between("age", 24, 35))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        min_number (Union[int, float]): The min number used in the predicate.
        max_number (Union[int, float]): The max number used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        not_between.__name__,
        path,
        (min_number, max_number),
        alias,
        lambda ctx: (f"NOT({ctx["path"]} > ${ctx["p0"]} AND " f"{ctx["path"]} < ${ctx["p1"]})"),
    )


def is_null(accessor_or_path: Union[str, Any], alias: Optional[str] = None) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is null.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: Optional[int]

        query.where(is_null(Human.age))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: Optional[int]

        query.where(is_null("age"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        is_null.__name__,
        path,
        tuple(),
        alias,
        lambda ctx: f"{ctx["path"]} IS NULL",
    )


def is_not_null(accessor_or_path: Union[str, Any], alias: Optional[str] = None) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is not null.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: Optional[int]

        query.where(is_not_null(Human.age))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: Optional[int]

        query.where(is_not_null("age"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        is_not_null.__name__,
        path,
        tuple(),
        alias,
        lambda ctx: f"{ctx["path"]} IS NOT NULL",
    )


def in_list(
    accessor_or_path: Union[str, Any],
    values_list: List[Any],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property matches one or more values from
    `values_list`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(in_list(Human.age, [1, 2, 3]))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(in_list("age", [1, 2, 3]))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        values_list (List[Any]): The list used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        in_list.__name__,
        path,
        (values_list,),
        alias,
        lambda ctx: f"ANY(i IN ${ctx["p0"]} WHERE {ctx["path"]} = i)",
    )


def not_in_list(
    accessor_or_path: Union[str, Any],
    values_list: List[Any],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property does not match any value from
    `values_list`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(not_in_list(Human.age, [1, 2, 3]))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            age: int

        query.where(not_in_list("age", [1, 2, 3]))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        values_list (List[Any]): The list used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        not_in_list.__name__,
        path,
        (values_list,),
        alias,
        lambda ctx: f"ALL(i IN ${ctx["p0"]} WHERE {ctx["path"]} <> i)",
    )


def all_(
    accessor_or_path: Union[str, Any],
    values_list: List[Any],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where all list items from property are also present in
    `values_list`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            favorite_numbers: List[int]

        query.where(all_(Human.favorite_numbers, [1, 2, 3]))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            favorite_numbers: List[int]

        query.where(all_("favorite_numbers", [1, 2, 3]))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        values_list (List[Any]): The list used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        all_.__name__,
        path,
        (values_list,),
        alias,
        lambda ctx: f"ALL(i IN {ctx["path"]} WHERE i IN ${ctx["p0"]})",
    )


def some(
    accessor_or_path: Union[str, Any],
    values_list: List[Any],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where some list items from property are also present in
    `values_list`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            favorite_numbers: List[int]

        query.where(some(Human.favorite_numbers, [1, 2, 3]))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            favorite_numbers: List[int]

        query.where(some("favorite_numbers", [1, 2, 3]))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        values_list (List[Any]): The list used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        some.__name__,
        path,
        (values_list,),
        alias,
        lambda ctx: f"ANY(i IN {ctx["path"]} WHERE i IN ${ctx["p0"]})",
    )


def none(
    accessor_or_path: Union[str, Any],
    values_list: List[Any],
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where no list items from property are present in
    `values_list`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            favorite_numbers: List[int]

        query.where(none(Human.favorite_numbers, [1, 2, 3]))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            favorite_numbers: List[int]

        query.where(none("favorite_numbers", [1, 2, 3]))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        values_list (List[Any]): The list used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        none.__name__,
        path,
        (values_list,),
        alias,
        lambda ctx: f"NOT(ANY(i IN {ctx["path"]} WHERE i IN ${ctx["p0"]}))",
    )


def contains(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is a substring of `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(contains(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(contains("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        contains.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"{ctx["path"]} CONTAINS ${ctx["p0"]}",
    )


def not_contains(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is not a substring of `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_contains(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_contains("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        not_contains.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"NOT({ctx["path"]} CONTAINS ${ctx["p0"]})",
    )


def icontains(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property is a (case-insensitive) substring of
    `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(icontains(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(icontains("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        icontains.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"toLower({ctx["path"]}) CONTAINS toLower(${ctx["p0"]})",
    )


def starts_with(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property starts with `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(starts_with(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(starts_with("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        starts_with.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"{ctx["path"]} STARTS WITH ${ctx["p0"]}",
    )


def not_starts_with(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property does not start with `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_starts_with(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_starts_with("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        not_starts_with.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"NOT({ctx["path"]} STARTS WITH ${ctx["p0"]})",
    )


def istarts_with(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property starts with `value` (case-insensitive).

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(istarts_with(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(istarts_with("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        istarts_with.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"toLower({ctx["path"]}) STARTS WITH toLower(${ctx["p0"]})",
    )


def ends_with(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property ends with `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(ends_with(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(ends_with("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        ends_with.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"{ctx["path"]} ENDS WITH ${ctx["p0"]}",
    )


def not_ends_with(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property does not end with `value`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_ends_with(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_ends_with("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        not_ends_with.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"NOT({ctx["path"]} ENDS WITH ${ctx["p0"]})",
    )


def iends_with(
    accessor_or_path: Union[str, Any],
    value: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property ends with `value` (case-insensitive).

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(iends_with(Human.name, "substr"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(iends_with("name", "substr"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        value (str): The string used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        iends_with.__name__,
        path,
        (value,),
        alias,
        lambda ctx: f"toLower({ctx["path"]}) ENDS WITH toLower(${ctx["p0"]})",
    )


def regex(
    accessor_or_path: Union[str, Any],
    regex_pattern: str,
    alias: Optional[str] = None,
) -> _Predicate:
    """
    Predicate helper for filtering entities where a property matches `regex_pattern`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(regex(Human.name, ".*\\.se"))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(regex("name", ".*\\.se"))
        ```

    Args:
        accessor_or_path (Union[str, Any]): A accessor or a property path.
        regex_pattern (str): The regex pattern used in the predicate.
        alias (Optional[str]): A optional alias for the referenced pattern. Defaults to `None`.

    Returns:
        _Predicate: Predicate used when compiling a query.
    """
    path = (
        accessor_or_path._full_path
        if isinstance(accessor_or_path, _PropertyAccessor)
        else accessor_or_path
    )

    return _Predicate(
        regex.__name__,
        path,
        (regex_pattern,),
        alias,
        lambda ctx: f"{ctx["path"]} =~ ${ctx["p0"]}",
    )


def not_(
    predicate: Union[_Predicate, _PredicateGroup],
) -> _PredicateGroup:
    """
    Predicate helper for negating another predicate.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_(eq(Human.name, "John")))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str

        query.where(not_(eq("name", John")))
        ```

    Args:
        predicate (Union[_Predicate, _PredicateGroup]): The predicate to negate.

    Returns:
        _PredicateGroup: Predicate group used when compiling a query.
    """
    return _PredicateGroup(not_.__name__, [predicate], lambda ctx: f"NOT({ctx["p0"]})")


def and_(
    *predicates: Union[_Predicate, _PredicateGroup],
) -> _PredicateGroup:
    """
    Predicate helper for combining multiple predicates with a `AND`.

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
        *predicates (Union[_Predicate, _PredicateGroup]): The predicates to combine.

    Returns:
        _PredicateGroup: Predicate group used when compiling a query.
    """
    return _PredicateGroup(
        and_.__name__, list(predicates), lambda ctx: f"({' AND '.join(ctx.values())})"
    )


def or_(
    *predicates: Union[_Predicate, _PredicateGroup],
) -> _PredicateGroup:
    """
    Predicate helper for combining multiple predicates with a `OR`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str
            age: int

        query.where(or_(eq(Human.name, "John"), gt(Human.age, 24)))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str
            age: int

        query.where(or_(eq("name", John"), gt("age", 24)))
        ```

    Args:
        *predicates (Union[_Predicate, _PredicateGroup]): The predicates to combine.

    Returns:
        _PredicateGroup: Predicate group used when compiling a query.
    """
    return _PredicateGroup(
        or_.__name__, list(predicates), lambda ctx: f"({' OR '.join(ctx.values())})"
    )


def xor_(
    *predicates: Union[_Predicate, _PredicateGroup],
) -> _PredicateGroup:
    """
    Predicate helper for combining multiple predicates with a `XOR`.

    Example:
        With a query accessor:
        ```python
        class Human(LoomiNode):
            name: str
            age: int

        query.where(xor_(eq(Human.name, "John"), gt(Human.age, 24)))
        ```

        With a property name:
        ```python
        class Human(LoomiNode):
            name: str
            age: int

        query.where(xor_(eq("name", John"), gt("age", 24)))
        ```

    Args:
        *predicates (Union[_Predicate, _PredicateGroup]): The predicates to combine.

    Returns:
        _PredicateGroup: Predicate group used when compiling a query.
    """
    return _PredicateGroup(
        xor_.__name__, list(predicates), lambda ctx: f"({' XOR '.join(ctx.values())})"
    )
