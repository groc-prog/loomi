# pylint: disable=missing-function-docstring

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi._internal._types import QueryModelType
from loomi._logger import logger
from loomi.query._context import QueryCompilationContext
from loomi.query._protocols import CompilableDescriptor, CompilableExpression
from loomi.query._templates import (
    ExpressionTemplate,
    LogicalExpressionTemplate,
    UnaryExpressionTemplate,
)

if TYPE_CHECKING:
    from loomi.query.db_function import DbFunction
    from loomi.query.descriptors import CompiledDescriptor
else:
    CompiledDescriptor = object
    DbFunction = object


@dataclass(frozen=True)
class _BaseQueryExpression(CompilableExpression):
    def __invert__(self) -> "InvertQueryExpression":
        from loomi.query.functions.comparison import not_

        return not_(self)

    def __and__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        from loomi.query.functions.comparison import and_

        return and_(self, other)

    def __or__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        from loomi.query.functions.comparison import or_

        return or_(self, other)

    def __xor__(self, other: "QueryExpression") -> "CompoundQueryExpression":
        from loomi.query.functions.comparison import xor

        return xor(self, other)


@dataclass(frozen=True)
class QueryExpression(_BaseQueryExpression):
    """A expression which can be compiled by a query builder."""

    descriptor: Union[CompilableDescriptor, DbFunction]
    template: ExpressionTemplate
    value: Any

    def _compile(self, ctx: QueryCompilationContext) -> str:
        from loomi.query.descriptors import DbFunction

        logger.debug("Compiling %s for template %s", self.__class__.__name__, self.template.name)

        if isinstance(self.descriptor, DbFunction):
            compiled = self.descriptor._compile(ctx, self.template.value, self.value)
            return compiled.template.format(wrapped=compiled.wrapped_path)

        compiled_descriptor: CompiledDescriptor = self.descriptor._compile(
            ctx, self.template.value, self.value
        )
        return compiled_descriptor.template.format(
            path=compiled_descriptor.variable_path, parameter=compiled_descriptor.parameter_name
        )


@dataclass(frozen=True)
class NullQueryExpression(_BaseQueryExpression):
    """A null-check expression which can be compiled by a query builder."""

    descriptor: CompilableDescriptor
    template: UnaryExpressionTemplate

    def _compile(self, ctx: QueryCompilationContext) -> str:
        logger.debug("Compiling %s for template %s", self.__class__.__name__, self.template.name)
        compiled_descriptor: CompiledDescriptor = self.descriptor._compile(
            ctx, self.template.value, None
        )
        return compiled_descriptor.template.format(
            path=compiled_descriptor.variable_path, parameter=compiled_descriptor.parameter_name
        )


@dataclass(frozen=True)
class InvertQueryExpression(_BaseQueryExpression):
    """A invert expression which can be compiled by a query builder."""

    expression: Union["CompoundQueryExpression", _BaseQueryExpression]

    def _compile(self, ctx: QueryCompilationContext) -> str:
        logger.debug("Compiling %s", self.__class__.__name__)
        compiled = self.expression._compile(ctx)
        return f"NOT({compiled})"


@dataclass(frozen=True)
class CompoundQueryExpression(CompilableExpression):
    """A compound expression which can be compiled by a query builder."""

    operator: LogicalExpressionTemplate
    expressions: List[Union["CompoundQueryExpression", _BaseQueryExpression]]

    def __and__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions.comparison import and_

        if self.operator == LogicalExpressionTemplate.AND:
            return and_(*self.expressions, other)

        return and_(self, other)

    def __or__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions.comparison import or_

        if self.operator == LogicalExpressionTemplate.OR:
            return or_(*self.expressions, other)

        return or_(self, other)

    def __xor__(
        self, other: Union["CompoundQueryExpression", QueryExpression]
    ) -> "CompoundQueryExpression":
        from loomi.query.functions.comparison import xor

        if self.operator == LogicalExpressionTemplate.XOR:
            return xor(*self.expressions, other)

        return xor(self, other)

    def __invert__(self) -> "InvertQueryExpression":
        from loomi.query.functions.comparison import not_

        return not_(self)

    def _compile(self, ctx: QueryCompilationContext) -> str:
        compiled: List[str] = []

        logger.debug(
            "Compiling %s with template %s for %d expressions",
            self.__class__.__name__,
            self.operator.name,
            len(self.expressions),
        )
        for expression in self.expressions:
            if isinstance(expression, CompoundQueryExpression):
                compiled.append(f"({expression._compile(ctx)})")
            else:
                compiled.append(expression._compile(ctx))

        return f" {self.operator.value} ".join(compiled)


@dataclass(frozen=True)
class CustomCypherExpression(CompilableExpression):
    """A custom cypher expression which can be compiled by a query builder."""

    template: str
    model_map: Dict[str, QueryModelType]
    parameter_map: Dict[str, Any]

    def _compile(self, ctx: QueryCompilationContext) -> str:
        logger.debug("Compiling models defined for custom cypher expression")
        expression_models_map = {
            placeholder: ctx.get_variable(model) for placeholder, model in self.model_map.items()
        }
        expression_parameters_map = {
            placeholder: f"${ctx.add_parameter(parameter)}"
            for placeholder, parameter in self.parameter_map.items()
        }

        return self.template.format(**expression_models_map, **expression_parameters_map)
