from typing import TYPE_CHECKING, Union

from loomi.models._internal._types import _ModelType

if TYPE_CHECKING:
    from loomi.query.helpers import AliasedModel
else:
    AliasedModel = object

_QueryModelType = Union[_ModelType, AliasedModel]
_NumericValue = Union[int, float]
