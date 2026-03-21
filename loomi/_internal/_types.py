from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from loomi.graph.node import Node
    from loomi.graph.relationship import Relationship
    from loomi.query.helpers import AliasedModel
else:
    AliasedModel = object
    Node = object
    Relationship = object


_ModelType = Union[Type[Node], Type[Relationship]]
_QueryModelType = Union[_ModelType, AliasedModel]

_NumericValue = Union[int, float]
