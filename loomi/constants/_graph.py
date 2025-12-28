from typing import Type, Union

from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

_ModelType = Union[Type[LoomiNode], Type[LoomiRelationship]]
