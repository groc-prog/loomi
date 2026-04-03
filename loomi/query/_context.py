from typing import Any, Dict

from loomi._internal.types import QueryModelType
from loomi._logger import logger
from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.query.alias import AliasedModel


class QueryCompilationContext:
    """Context scoped to a query compilation."""

    server_type: ServerType
    parameters: Dict[str, Any]
    _variable_counter: int
    _models_to_vars: Dict[QueryModelType, str]

    def __init__(self, server_type: ServerType) -> None:
        self.server_type = server_type
        self._variable_counter = 0
        self._models_to_vars = {}
        self.parameters = {}

    def force_increment_variable_counter(self, amount: int = 1) -> None:
        """
        Used to manually increment the internal counter for parameter names.

        Args:
            amount (int): The number by which the counter will be incremented. Defaults to 1.
        """
        logger.debug("Force-incrementing internal variable counter by %d", amount)
        self._variable_counter = self._variable_counter + amount

    def add_parameter(self, value: Any) -> str:
        """
        Adds a parameter with a auto-generated name.

        Args:
            value (Any): The value for the parameter.

        Returns:
            str: The auto-generated parameter name.
        """
        parameter_name = f"p{len(self.parameters.keys())}"
        logger.debug("Adding new parameter %s to expression context", parameter_name)
        self.parameters[parameter_name] = value

        return parameter_name

    def get_variable(self, model: QueryModelType) -> str:
        """
        Returns the variable used for a given model.

        Args:
            model (QueryModelType): The model to register.

        Raises:
            QueryError: If the model has not been registered yet.

        Returns:
            str: The variable.
        """
        if model not in self._models_to_vars:
            raise QueryError(f"Model {model.__name__} is not known in the current query context")

        return self._models_to_vars[model]

    def add_model(self, model: QueryModelType) -> None:
        """
        Adds a new model to the context. Models have to be added with this method before they can be
        referenced in compiled expressions.

        Args:
            model (QueryModelType): The model to register.

        Raises:
            QueryError: If the variable used for the model already exists.
        """
        logger.debug(
            "Registering %s with expression context",
            (f"alias {model._alias}" if isinstance(model, AliasedModel) else model.__name__),
        )

        variable = model._alias if isinstance(model, AliasedModel) else f"v{self._variable_counter}"
        if variable in set(self._models_to_vars.values()):
            logger.warning(
                "Variable %s has already been defined. If you are using a aliased model "
                ", make sure it's alias is unique",
                variable,
            )
            return

        self._variable_counter = self._variable_counter + 1
        self._models_to_vars[model] = variable
        logger.debug("Model added as variable %s", variable)
