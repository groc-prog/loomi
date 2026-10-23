from typing import Any, Dict

from loomi._core.types import QueryModelType
from loomi.constants import ServerType
from loomi.exceptions import QueryError
from loomi.logger import get_logger

logger = get_logger("query_api")


class CompilationContext:
    server_type: ServerType
    __parameters: Dict[str, Any]
    __variable_counter: int
    __models_to_vars: Dict[QueryModelType, str]

    def __init__(self, server_type: ServerType) -> None:
        self.server_type = server_type
        self.__variable_counter = 0
        self.__models_to_vars = {}
        self.__parameters = {}

    def force_increment_variable_counter(self, amount: int = 1) -> None:
        logger.debug("Force-incrementing internal variable counter by %d", amount)
        self.__variable_counter = self.__variable_counter + amount

    def add_parameter(self, value: Any) -> str:
        parameter_name = f"p{len(self.__parameters.keys())}"
        logger.debug("Adding new parameter %s to expression context", parameter_name)
        self.__parameters[parameter_name] = value

        return parameter_name

    def add_model(self, model: QueryModelType) -> None:
        logger.debug("Registering %s with expression context", f"model {model.__name__}")

        variable = f"v{self.__variable_counter}"
        if variable in set(self.__models_to_vars.values()):
            logger.warning(
                "Variable %s has already been defined",
                variable,
            )
            return

        self.__variable_counter = self.__variable_counter + 1
        self.__models_to_vars[model] = variable
        logger.debug("Model added as variable %s", variable)

    def get_variable(self, model: QueryModelType) -> str:
        if model not in self.__models_to_vars:
            raise QueryError(f"Model {model.__name__} is not known in the current query context")

        return self.__models_to_vars[model]

    def get_variable_count(self) -> int:
        return self.__variable_counter

    def get_parameters(self) -> Dict[str, Any]:
        return self.__parameters
