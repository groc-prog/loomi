from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Protocol, overload, runtime_checkable

if TYPE_CHECKING:
    from loomi.query_api._core.context import CompilationContext
else:
    CompilationContext = object


@dataclass(frozen=True)
class CompiledDescriptor:
    """The compiled version for a given descriptor."""

    template: str
    variable_path: str
    parameter_name: Optional[str]


@dataclass(frozen=True)
class CompiledDbFunction:
    """The compiled version for a given Db function."""

    template: str
    wrapped_path: str


@runtime_checkable
class CompilableDescriptor(Protocol):
    """Protocol implemented by descriptors making them compilable."""

    def _compile_descriptor(
        self, ctx: CompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledDescriptor: ...


@runtime_checkable
class CompilableExpression(Protocol):
    """Protocol implemented by expressions making them compilable."""

    def _compile_expression(self, ctx: CompilationContext) -> str: ...


@runtime_checkable
class CompilableDbFunction(Protocol):
    """Protocol implemented by DB functions making them compilable."""

    @overload
    def _compile_db_function(self, ctx: CompilationContext) -> CompiledDbFunction: ...

    @overload
    def _compile_db_function(
        self, ctx: CompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledDbFunction: ...

    def _compile_db_function(
        self,
        ctx: CompilationContext,
        expression_template: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> CompiledDbFunction: ...
