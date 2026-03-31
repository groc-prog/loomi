# pylint: disable=unnecessary-ellipsis

from dataclasses import dataclass
from typing import Any, Optional, Protocol, runtime_checkable

from loomi.query._context import QueryCompilationContext


@dataclass(frozen=True)
class CompiledDescriptor:
    """The compiled version for a given descriptor."""

    template: str
    variable_path: str
    parameter_name: Optional[str]


@runtime_checkable
class CompilableExpression(Protocol):
    """Protocol implemented by expressions making them compilable."""

    def _compile(self, ctx: QueryCompilationContext) -> str: ...


@runtime_checkable
class CompilableDescriptor(Protocol):
    """Protocol implemented by descriptors making them compilable."""

    def _compile(
        self, ctx: QueryCompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledDescriptor: ...
