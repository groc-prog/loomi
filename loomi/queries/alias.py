import re
from dataclasses import dataclass

from loomi.exceptions import QueryError
from loomi.models._internal._types import _ModelType
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship


@dataclass
class LoomiQueryAlias:
    """
    Query alias for the query builder. Allows referencing the same model multiple times in the
    same query and other advanced query manipulation.
    """

    _model_type: _ModelType
    _hash: str
    _alias: str


def query_alias(model: _ModelType, alias: str) -> LoomiQueryAlias:
    """
    Creates a new query alias for the defined model and the defined variable name.

    Args:
        model (Union[Type[LoomiNode], Type[LoomiRelationship]]): The model used for the alias.
        alias (str): The variable name used in the query. Each alias must be unique in each query.

    Raises:
        QueryError: If a invalid or reserved alias name is passed. Reserved alias names are
        n_<any number> for node models and r_<any number> for relationship models.

    Returns:
        LoomiQueryAlias: Model alias which can be used with query builders.
    """
    if issubclass(model, LoomiNode) and re.match(r"^n_\d+$", alias):
        raise QueryError(
            f"{alias} uses a reserved format. The format 'n_<any number>' can not be used as a "
            "alias"
        )

    if issubclass(model, LoomiRelationship) and re.match(r"^r_\d+$", alias):
        raise QueryError(
            f"{alias} uses a reserved format. The format 'r_<any number>' can not be used as a "
            "alias"
        )

    return LoomiQueryAlias(model, f"{model._hash}_{alias}", alias)
