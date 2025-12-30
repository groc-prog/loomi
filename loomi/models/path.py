from typing import TYPE_CHECKING, Any, Iterator, Tuple, Union

from neo4j.graph import EntitySetView, Graph, Node, Relationship

from loomi._driver._graph import LoomiGraph
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

if TYPE_CHECKING:
    from loomi.clients._base import _LoomiBaseClient
else:
    _LoomiBaseClient = object

LoomiPathNode = Union[LoomiNode, Node]
LoomiPathRelationship = Union[LoomiRelationship, Relationship]


class LoomiPath:
    """Graph path containing resolved Loomi nodes."""

    __client: _LoomiBaseClient
    _nodes: Tuple[LoomiPathNode, ...]
    _relationships: Tuple[LoomiPathRelationship, ...]
    _graph: Graph

    def __init__(
        self,
        client: _LoomiBaseClient,
        nodes: Tuple[LoomiPathNode, ...],
        relationships: Tuple[LoomiPathRelationship, ...],
        graph: Graph,
    ):
        self.__client = client
        self._nodes = nodes
        self._relationships = relationships
        self._graph = graph

    def __repr__(self) -> str:
        return f"<LoomiPath start={self.start_node!r} end={self.end_node!r} " f"size={len(self)}>"

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

    def __iter__(self) -> Iterator[LoomiPathRelationship]:
        return iter(self._relationships)

    @property
    def graph(self) -> LoomiGraph:
        """The `LoomiGraph` to which this path belongs."""
        graph = LoomiGraph()

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
        graph._node_set_view = EntitySetView(graph._nodes)
        graph._relationship_set_view = EntitySetView(graph._relationships)

        return graph

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
