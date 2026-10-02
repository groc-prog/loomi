# pylint: disable=missing-function-docstring

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi._core.types import QueryModelType
from loomi._logger import logger
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableDescriptor,
    CompilableExpression,
)
from loomi.query_api._core.templates import (
    ArithmeticExpressionTemplate,
    ExpressionTemplate,
    LogicalExpressionTemplate,
    UnaryExpressionTemplate,
)

if TYPE_CHECKING:
    from loomi.query_api._core.protocols import CompiledDescriptor
else:
    CompiledDescriptor = object


@dataclass(frozen=True)
class _BaseExpression(CompilableExpression):
    def __invert__(self) -> "InvertExpression":
        from loomi.query_api.functions.comparison import not_

        return not_(self)

    def __and__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import and_

        return and_(self, other)

    def __or__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import or_

        return or_(self, other)

    def __xor__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import xor

        return xor(self, other)


@dataclass(frozen=True)
class Expression(_BaseExpression):
    """A expression which can be compiled by a query builder."""

    descriptor: Union[CompilableDescriptor, CompilableDbFunction]
    template: Union[ExpressionTemplate, ArithmeticExpressionTemplate]
    value: Any

    def _compile_expression(self, ctx: CompilationContext) -> str:
        logger.debug("Compiling %s for template %s", self.__class__.__name__, self.template.name)

        if isinstance(self.descriptor, CompilableDbFunction):
            compiled = self.descriptor._compile_db_function(ctx, self.template.value, self.value)
            return compiled.template.format(wrapped=compiled.wrapped_path)

        compiled_descriptor: CompiledDescriptor = self.descriptor._compile_descriptor(
            ctx, self.template.value, self.value
        )
        return compiled_descriptor.template.format(
            path=compiled_descriptor.variable_path, parameter=compiled_descriptor.parameter_name
        )


@dataclass(frozen=True)
class NullExpression(_BaseExpression):
    """A null-check expression which can be compiled by a query builder."""

    descriptor: CompilableDescriptor
    template: UnaryExpressionTemplate

    def _compile_expression(self, ctx: CompilationContext) -> str:
        logger.debug("Compiling %s for template %s", self.__class__.__name__, self.template.name)
        compiled_descriptor: CompiledDescriptor = self.descriptor._compile_descriptor(
            ctx, self.template.value, None
        )
        return compiled_descriptor.template.format(
            path=compiled_descriptor.variable_path, parameter=compiled_descriptor.parameter_name
        )


@dataclass(frozen=True)
class InvertExpression(_BaseExpression):
    """A invert expression which can be compiled by a query builder."""

    expression: Union["CompoundExpression", _BaseExpression]

    def _compile_expression(self, ctx: CompilationContext) -> str:
        logger.debug("Compiling %s", self.__class__.__name__)
        compiled = self.expression._compile_expression(ctx)
        return f"NOT({compiled})"


@dataclass(frozen=True)
class CompoundExpression(CompilableExpression):
    """A compound expression which can be compiled by a query builder."""

    operator: LogicalExpressionTemplate
    expressions: List[Union["CompoundExpression", _BaseExpression]]

    def __and__(self, other: Union["CompoundExpression", Expression]) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import and_

        if self.operator == LogicalExpressionTemplate.AND:
            return and_(*self.expressions, other)

        return and_(self, other)

    def __or__(self, other: Union["CompoundExpression", Expression]) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import or_

        if self.operator == LogicalExpressionTemplate.OR:
            return or_(*self.expressions, other)

        return or_(self, other)

    def __xor__(self, other: Union["CompoundExpression", Expression]) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import xor

        if self.operator == LogicalExpressionTemplate.XOR:
            return xor(*self.expressions, other)

        return xor(self, other)

    def __invert__(self) -> "InvertExpression":
        from loomi.query_api.functions.comparison import not_

        return not_(self)

    def _compile_expression(self, ctx: CompilationContext) -> str:
        compiled: List[str] = []

        logger.debug(
            "Compiling %s with template %s for %d expressions",
            self.__class__.__name__,
            self.operator.name,
            len(self.expressions),
        )
        for expression in self.expressions:
            if isinstance(expression, CompoundExpression):
                compiled.append(f"({expression._compile_expression(ctx)})")
            else:
                compiled.append(expression._compile_expression(ctx))

        return f" {self.operator.value} ".join(compiled)


@dataclass(frozen=True)
class CustomCypherExpression(CompilableExpression):
    """A custom cypher expression which can be compiled by a query builder."""

    template: str
    model_map: Dict[str, QueryModelType]
    parameter_map: Dict[str, Any]

    def _compile_expression(self, ctx: CompilationContext) -> str:
        logger.debug("Compiling models defined for custom cypher expression")
        expression_models_map = {
            placeholder: ctx.get_variable(model) for placeholder, model in self.model_map.items()
        }
        expression_parameters_map = {
            placeholder: f"${ctx.add_parameter(parameter)}"
            for placeholder, parameter in self.parameter_map.items()
        }

        return self.template.format(**expression_models_map, **expression_parameters_map)
