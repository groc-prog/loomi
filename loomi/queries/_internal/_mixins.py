from typing import TYPE_CHECKING, Optional, Type, Union, overload

from loomi.exceptions import ModelInitializationError, QueryError
from loomi.models._internal._types import _ModelType
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from loomi.queries.alias import LoomiQueryAlias

if TYPE_CHECKING:
    from loomi.queries.builder import _MatchState, _SetState, _StateProtocol
else:
    _MatchState = object
    _SetState = object
    _StateProtocol = object


class _HasMatch(_StateProtocol):
    @overload
    def match(self, model: Union[Type[LoomiNode], LoomiQueryAlias]) -> _MatchState: ...

    @overload
    def match(
        self,
        model: Union[Type[LoomiRelationship], LoomiQueryAlias],
        start_node: Optional[Union[Type[LoomiNode], LoomiQueryAlias]] = None,
        end_node: Optional[Union[Type[LoomiNode], LoomiQueryAlias]] = None,
    ) -> _MatchState: ...

    def match(
        self,
        model: Union[_ModelType, LoomiQueryAlias],
        start_node: Optional[Union[Type[LoomiNode], LoomiQueryAlias]] = None,
        end_node: Optional[Union[Type[LoomiNode], LoomiQueryAlias]] = None,
    ) -> _MatchState:
        """
        Adds a new `MATCH` pattern to the builders context.

        Args:
            model (Union[Type[LoomiNode], Type[LoomiRelationship], LoomiQueryAlias]): The model or
            query alias to use in the match pattern.
            start_node (Union[Type[LoomiNode], LoomiQueryAlias]): When `model` is a relationship
            model or alias, this sets the start node of the relationship pattern.
            end_node (Union[Type[LoomiNode], LoomiQueryAlias]): When `model` is a relationship
            model or alias, this sets the end node of the relationship pattern.

        Raises:
            QueryError: If a invalid model or query alias is provided.
        """
        from loomi.queries.builder import _MatchState

        model_type = model._model_type if isinstance(model, LoomiQueryAlias) else model
        variable_name = self._state.get_existing_or_new_variable(model)

        if issubclass(model_type, LoomiNode):
            pattern = self._build_node_pattern(model_type, variable_name)
            self._state.match_patterns.append(pattern)
        elif issubclass(model_type, LoomiRelationship):
            start_node_pattern = "()"
            end_node_pattern = "()"

            if start_node is not None:
                start_node_model_type = (
                    start_node._model_type
                    if isinstance(start_node, LoomiQueryAlias)
                    else start_node
                )
                start_node_variable_name = self._state.get_existing_or_new_variable(start_node)

                if not issubclass(start_node_model_type, LoomiNode):
                    raise QueryError(f"Expected start node to be {LoomiNode.__name__}")

                start_node_pattern = self._build_node_pattern(
                    start_node_model_type, start_node_variable_name
                )

            if end_node is not None:
                end_node_model_type = (
                    end_node._model_type if isinstance(end_node, LoomiQueryAlias) else end_node
                )
                end_node_variable_name = self._state.get_existing_or_new_variable(end_node)

                if not issubclass(end_node_model_type, LoomiNode):
                    raise QueryError(f"Expected end node to be {LoomiNode.__name__}")

                end_node_pattern = self._build_node_pattern(
                    end_node_model_type, end_node_variable_name
                )

            relationship_pattern = self._build_relationship_pattern(model_type, variable_name)
            self._state.match_patterns.append(
                f"{start_node_pattern}-{relationship_pattern}->{end_node_pattern}"
            )
        else:
            raise QueryError(
                f"Expected provided model to be {LoomiNode.__name__}, "
                f"{LoomiRelationship.__name__} or a valid {LoomiQueryAlias.__name__}"
            )

        return _MatchState(self._state)

    def _build_node_pattern(self, model_type: Type[LoomiNode], variable_name: str) -> str:
        labels = model_type.loomi_config.get("labels")
        if labels is None:
            raise ModelInitializationError(
                f"Model {model_type.__name__} not fully initialized. Expected labels to be "
                "defined"
            )

        return f"({variable_name}:{':'.join(labels)})"

    def _build_relationship_pattern(
        self, model_type: Type[LoomiRelationship], variable_name: str
    ) -> str:
        type_ = model_type.loomi_config.get("type")
        if type_ is None:
            raise ModelInitializationError(
                f"Model {model_type.__name__} not fully initialized. Expected type to be defined"
            )

        return f"[{variable_name}:{type_}]"


class _HasSet(_StateProtocol):
    pass
