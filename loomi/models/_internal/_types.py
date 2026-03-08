from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from loomi.models.node import Node
    from loomi.models.relationship import Relationship
else:
    Node = object
    Relationship = object

_ModelType = Union[Type[Node], Type[Relationship]]
