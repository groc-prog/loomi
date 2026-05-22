# pylint: disable=unnecessary-ellipsis

from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from loomi.query._context import CompilationContext
    from loomi.query.descriptors import CompiledDescriptor
else:
    CompiledDescriptor = object
    CompilationContext = object


@runtime_checkable
class CompilableExpression(Protocol):
    """Protocol implemented by expressions making them compilable."""

    def _compile(self, ctx: CompilationContext) -> str: ...


@runtime_checkable
class CompilableDescriptor(Protocol):
    """Protocol implemented by descriptors making them compilable."""

    def _compile(
        self, ctx: CompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledDescriptor: ...
