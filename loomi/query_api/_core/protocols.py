from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Protocol, Union, runtime_checkable

from loomi.logger import get_logger

if TYPE_CHECKING:
    from loomi.query_api._core.context import CompilationContext
else:
    CompilationContext = object


logger = get_logger("query_api")


@dataclass(frozen=True)
class CompiledDescriptor:
    """The compiled version for a given descriptor."""

    full_template: str
    variable_path: str
    variable: str
    full_path: Optional[str]


@dataclass(frozen=True)
class CompiledExpression:
    """The compiled version for a given descriptor."""

    outer_template: str
    expression_template: str
    expression_variable: str
    full_path: Optional[str]

    def to_query_string(self) -> str:
        """
        Generates a query string from the compiled expression.

        Returns:
            str: The part of the query string represented by this compiled expression.
        """
        logger.debug(
            "Formatting compiled expression to query string. "
            "outer template %s; "
            "expression template %s; "
            "expression variable %s",
            self.outer_template,
            self.expression_template,
            self.expression_variable,
        )
        compiled_expression_template = self.expression_template.format(
            variable=self.expression_variable
        )
        return self.outer_template.format(innermost_template=compiled_expression_template)


@dataclass(frozen=True)
class CompiledDbFunction:
    """The compiled version for a given Db function."""

    full_template: str
    inserted_parameter: Optional[str]

    def to_query_string(self) -> str:
        """
        Generates a query string from the compiled expression.

        Returns:
            str: The part of the query string represented by this compiled expression.
        """
        logger.debug(
            "Formatting compiled db function to query string. parameter %s",
            self.inserted_parameter,
        )
        return self.full_template.format(variable_or_value=f"${self.inserted_parameter}")


@runtime_checkable
class CompilableDescriptor(Protocol):
    """Protocol implemented by descriptors making them compilable."""

    def _compile_descriptor(self, ctx: CompilationContext) -> CompiledDescriptor: ...


@runtime_checkable
class CompilableExpression(Protocol):
    """Protocol implemented by expressions making them compilable."""

    def _compile_expression(self, ctx: CompilationContext) -> CompiledExpression: ...


@runtime_checkable
class CompilableDbFunction(Protocol):
    """Protocol implemented by DB functions making them compilable."""

    def _compile_db_function(
        self, ctx: CompilationContext
    ) -> Union[CompiledDescriptor, CompiledDbFunction]: ...
