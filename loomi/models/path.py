from typing import Any, Generic, Iterator, Tuple, TypeVar

from neo4j.graph import Graph

from loomi.exceptions import EmptyGraphError, NonHydratedModelError
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

N = TypeVar("N", bound=LoomiNode)
R = TypeVar("R", bound=LoomiRelationship)


class LoomiPath(Generic[N, R]):
    """Graph path containing resolved Loomi nodes."""

    _nodes: Tuple[N]
    _relationships: Tuple[R]

    def __repr__(self) -> str:
        return (
            f"<Path start={self.start_node!r} end={self.end_node!r} "
            f"size={len(self)}>"
        )

    def __eq__(self, other: Any) -> bool:
        try:
            return (
                self.start_node == other.start_node
                and self.relationships == other.relationships
            )
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        value = hash(self._nodes[0])
        for relationship in self._relationships:
            value ^= hash(relationship)
        return value

    def __len__(self) -> int:
        return len(self._relationships)

    def __iter__(self) -> Iterator[R]:
        return iter(self._relationships)

    @property
    def graph(self) -> Graph:
        """The `Graph` to which this path belongs."""
        if len(self._nodes) == 0:
            raise EmptyGraphError("No nodes found in graph")

        graph = self._nodes[0].graph
        if graph is None:
            raise NonHydratedModelError("Non hydrated model found in path")

        return graph

    @property
    def nodes(self) -> tuple[N, ...]:
        """The sequence of `LoomiNode` objects in this path."""
        return self._nodes

    @property
    def start_node(self) -> N:
        """The first `LoomiNode` in this path."""
        return self._nodes[0]

    @property
    def end_node(self) -> N:
        """The last `LoomiNode` in this path."""
        return self._nodes[-1]

    @property
    def relationships(self) -> tuple[R, ...]:
        """The sequence of `LoomiRelationship` objects in this path."""
        return self._relationships
