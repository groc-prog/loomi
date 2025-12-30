from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from loomi.models.node import LoomiNode
    from loomi.models.relationship import LoomiRelationship
else:
    LoomiNode = object
    LoomiRelationship = object

_ModelType = Union[Type[LoomiNode], Type[LoomiRelationship]]
