from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from loomi.graph.node import Node
    from loomi.graph.relationship import Relationship
else:
    Node = object
    Relationship = object


ModelType = Union[Type[Node], Type[Relationship]]
QueryModelType = ModelType

NumericValue = Union[int, float]
TResultKey = int | str
