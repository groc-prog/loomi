from typing import Dict, Tuple, Type, Union, cast

from neo4j.graph import EntitySetView, Node, Relationship

from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship


class LoomiGraph:
    """
    A graph of nodes and relationships transformed into Loomi models. Provides the same interface
    as `neo4j.graph.Graph`.
    """

    _nodes: Dict[str, Union[LoomiNode, Node]]
    _relationships: Dict[str, Union[LoomiRelationship, Relationship]]
    _relationship_types: Dict[str, Type[Union[LoomiRelationship, Relationship]]]
    _node_set_view: EntitySetView[Union[LoomiNode, Node]]
    _relationship_set_view: EntitySetView[Union[LoomiRelationship, Relationship]]

    def __init__(self):
        self._nodes = {}
        self._relationships = {}
        self._relationship_types = {}
        self._node_set_view = EntitySetView(self._nodes)
        self._relationship_set_view = EntitySetView(self._relationships)

    @property
    def nodes(self) -> EntitySetView[Union[LoomiNode, Node]]:
        """See `neo4j.graph.Graph.nodes`."""
        return self._node_set_view

    @property
    def relationships(self) -> EntitySetView[Union[LoomiRelationship, Relationship]]:
        """See `neo4j.graph.Graph.relationships`."""
        return self._relationship_set_view

    def relationship_type(
        self, name: str
    ) -> Type[Union[LoomiRelationship, Relationship]]:
        """See `neo4j.graph.Graph.relationship_type`."""
        try:
            cls = self._relationship_types[name]
        except KeyError:
            cls = self._relationship_types[name] = cast(
                Type[Relationship], type(str(name), (Relationship,), {})
            )
        return cls

    def __reduce__(self):
        state = self.__dict__.copy()
        relationship_types = tuple(state.pop("_relationship_types", {}).keys())
        restore_args = (relationship_types,)
        return LoomiGraph._restore, restore_args, state

    @staticmethod
    def _restore(relationship_types: Tuple[str, ...]) -> "LoomiGraph":
        graph = LoomiGraph.__new__(LoomiGraph)
        graph.__dict__["_relationship_types"] = {
            name: type(str(name), (Relationship,), {}) for name in relationship_types
        }
        return graph
