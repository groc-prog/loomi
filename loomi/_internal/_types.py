from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from loomi.graph.node import Node
    from loomi.graph.relationship import Relationship
    from loomi.query.functions import AliasedModel
else:
    AliasedModel = object
    Node = object
    Relationship = object


ModelType = Union[Type[Node], Type[Relationship]]
QueryModelType = Union[ModelType, AliasedModel]

NumericValue = Union[int, float]
TResultKey = int | str
