# pylint: disable=unnecessary-ellipsis

from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

from loomi.query._context import QueryCompilationContext

if TYPE_CHECKING:
    from loomi.query.descriptors import CompiledDescriptor
else:
    CompiledDescriptor = object


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
