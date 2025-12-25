from typing import Any, Iterator, Tuple, Union

from neo4j.graph import Graph, Node, Relationship

from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

LoomiPathNode = Union[LoomiNode, Node]
LoomiPathRelationship = Union[LoomiRelationship, Relationship]


class LoomiPath:
    """Graph path containing resolved Loomi nodes."""

    _nodes: Tuple[LoomiPathNode, ...]
    _relationships: Tuple[LoomiPathRelationship, ...]
    _graph: Graph

    def __init__(
        self,
        nodes: Tuple[LoomiPathNode, ...],
        relationships: Tuple[LoomiPathRelationship, ...],
        graph: Graph,
    ):
        self._nodes = nodes
        self._relationships = relationships
        self._graph = graph

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

    def __iter__(self) -> Iterator[LoomiPathRelationship]:
        return iter(self._relationships)

    @property
    def graph(self) -> Graph:
        """The `Graph` to which this path belongs."""
        return self._graph

    @property
    def nodes(self) -> tuple[LoomiPathNode, ...]:
        """The sequence of `LoomiNode` objects in this path."""
        return self._nodes

    @property
    def start_node(self) -> LoomiPathNode:
        """The first `LoomiNode` in this path."""
        return self._nodes[0]

    @property
    def end_node(self) -> LoomiPathNode:
        """The last `LoomiNode` in this path."""
        return self._nodes[-1]

    @property
    def relationships(self) -> tuple[LoomiPathRelationship, ...]:
        """The sequence of `LoomiRelationship` objects in this path."""
        return self._relationships
