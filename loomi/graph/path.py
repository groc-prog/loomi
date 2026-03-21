from typing import TYPE_CHECKING, Any, Iterator, Tuple, Union

import neo4j.graph

from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship

if TYPE_CHECKING:
    from loomi._internal._base_client import _BaseClient
else:
    _BaseClient = object

PathNode = Union[Node, neo4j.graph.Node]
PathRelationship = Union[Relationship, neo4j.graph.Relationship]


class Path:
    """Graph path containing resolved Loomi nodes."""

    __client: _BaseClient
    _nodes: Tuple[PathNode, ...]
    _relationships: Tuple[PathRelationship, ...]
    _graph: neo4j.graph.Graph

    def __init__(
        self,
        client: _BaseClient,
        nodes: Tuple[PathNode, ...],
        relationships: Tuple[PathRelationship, ...],
        graph: neo4j.graph.Graph,
    ):
        self.__client = client
        self._nodes = nodes
        self._relationships = relationships
        self._graph = graph

    def __repr__(self) -> str:
        return f"<Path start={self.start_node!r} end={self.end_node!r} " f"size={len(self)}>"

    def __eq__(self, other: Any) -> bool:
        try:
            return self.start_node == other.start_node and self.relationships == other.relationships
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        value = hash(self._nodes[0])
        for relationship in self._relationships:
            value ^= hash(relationship)
        return value

    def __len__(self) -> int:
        return len(self._relationships)

    def __iter__(self) -> Iterator[PathRelationship]:
        return iter(self._relationships)

    @property
    def graph(self) -> Graph:
        """The `Graph` to which this path belongs."""
        graph = Graph()

        graph._nodes = {
            element_id: self.__client._transform_entity(node)
            for element_id, node in self._graph._nodes.items()
        }
        graph._relationships = {
            element_id: self.__client._transform_entity(relationship)
            for element_id, relationship in self._graph._relationships.items()
        }
        graph._relationship_types = {
            type_: self.__client._relationship_type_to_model(type_) or relationship
            for type_, relationship in self._graph._relationship_types.items()
        }
        graph._node_set_view = neo4j.graph.EntitySetView(graph._nodes)
        graph._relationship_set_view = neo4j.graph.EntitySetView(graph._relationships)

        return graph

    @property
    def nodes(self) -> tuple[PathNode, ...]:
        """The sequence of `Node` objects in this path."""
        return self._nodes

    @property
    def start_node(self) -> PathNode:
        """The first `Node` in this path."""
        return self._nodes[0]

    @property
    def end_node(self) -> PathNode:
        """The last `Node` in this path."""
        return self._nodes[-1]

    @property
    def relationships(self) -> tuple[PathRelationship, ...]:
        """The sequence of `Relationship` objects in this path."""
        return self._relationships
