from typing import Dict, Tuple, Type, Union, cast

import neo4j.graph

from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class Graph:
    """
    A graph of nodes and relationships transformed into Loomi models. Provides the same interface
    as `neo4j.graph.Graph`.
    """

    _nodes: Dict[str, Union[Node, neo4j.graph.Node]]
    _relationships: Dict[str, Union[Relationship, neo4j.graph.Relationship]]
    _relationship_types: Dict[str, Type[Union[Relationship, neo4j.graph.Relationship]]]
    _node_set_view: neo4j.graph.EntitySetView[Union[Node, neo4j.graph.Node]]
    _relationship_set_view: neo4j.graph.EntitySetView[Union[Relationship, neo4j.graph.Relationship]]

    def __init__(self):
        self._nodes = {}
        self._relationships = {}
        self._relationship_types = {}
        self._node_set_view = neo4j.graph.EntitySetView(self._nodes)
        self._relationship_set_view = neo4j.graph.EntitySetView(self._relationships)

    @property
    def nodes(self) -> neo4j.graph.EntitySetView[Union[Node, neo4j.graph.Node]]:
        """Property providing the same interface as `neo4j.graph.Graph.nodes`."""
        return self._node_set_view

    @property
    def relationships(
        self,
    ) -> neo4j.graph.EntitySetView[Union[Relationship, neo4j.graph.Relationship]]:
        """Property providing the same interface as `neo4j.graph.Graph.relationships`."""
        return self._relationship_set_view

    def relationship_type(self, name: str) -> Type[Union[Relationship, neo4j.graph.Relationship]]:
        """Property providing the same interface as `neo4j.graph.Graph.relationship_type`."""
        try:
            cls = self._relationship_types[name]
        except KeyError:
            cls = self._relationship_types[name] = cast(
                Type[neo4j.graph.Relationship], type(str(name), (neo4j.graph.Relationship,), {})
            )
        return cls

    def __reduce__(self):
        state = self.__dict__.copy()
        relationship_types = tuple(state.pop("_relationship_types", {}).keys())
        restore_args = (relationship_types,)
        return Graph._restore, restore_args, state

    @staticmethod
    def _restore(relationship_types: Tuple[str, ...]) -> "Graph":
        graph = Graph.__new__(Graph)
        graph.__dict__["_relationship_types"] = {
            name: type(str(name), (neo4j.graph.Relationship,), {}) for name in relationship_types
        }
        return graph
