# pylint: disable=unnecessary-ellipsis

from typing import Any, Optional, Protocol, Tuple, runtime_checkable

from loomi.query._context import ExpressionContext

CompilationPlan = Tuple[str, str, Optional[str]]


@runtime_checkable
class CompilableDescriptor(Protocol):
    """Protocol implemented by descriptors making them compilable."""

    def _compile(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> str: ...

    def _compilation_plan(
        self, ctx: ExpressionContext, expression_template: str, value: Optional[Any]
    ) -> CompilationPlan: ...


@runtime_checkable
class CompilableExpression(Protocol):
    """Protocol implemented by expressions making them compilable."""

    def _compile(self, ctx: ExpressionContext) -> str: ...
