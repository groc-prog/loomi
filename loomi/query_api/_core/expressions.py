# pylint: disable=missing-function-docstring

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from loomi._core.types import QueryModelType
from loomi._logger import logger
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.protocols import (
    CompilableAndRunnableExpression,
    CompilableDbFunction,
    CompilableDescriptor,
    CompiledDbFunction,
    CompiledExpression,
    RunnableExpression,
)
from loomi.query_api._core.templates import (
    ArithmeticExpressionTemplate,
    ExpressionTemplate,
    LogicalExpressionTemplate,
)

if TYPE_CHECKING:
    from loomi.query_api._core.protocols import CompiledDescriptor
else:
    CompiledDescriptor = object


@dataclass(frozen=True)
class ExpressionMixin:
    """Expression mixin providing shared overloads for common magic methods."""

    def __invert__(self) -> CompilableAndRunnableExpression:
        from loomi.query_api.functions.comparison import not_

        return not_(cast(CompilableAndRunnableExpression, self))

    def __and__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import and_

        return and_(cast(CompilableAndRunnableExpression, self), other)

    def __or__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import or_

        return or_(cast(CompilableAndRunnableExpression, self), other)

    def __xor__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import xor

        return xor(cast(CompilableAndRunnableExpression, self), other)


@dataclass(frozen=True)
class Expression(ExpressionMixin, CompilableAndRunnableExpression):
    """A expression which can be compiled by a query builder."""

    descriptor: Union[CompilableDescriptor, CompilableDbFunction]
    template: Union[ExpressionTemplate, ArithmeticExpressionTemplate]
    value: Any

    def _compile_expression(self, ctx: CompilationContext) -> CompiledExpression:
        logger.debug("Compiling %s for template %s", self.__class__.__name__, self.template.name)

        if isinstance(self.descriptor, CompilableDbFunction):
            compiled_descriptor = cast(
                CompiledDescriptor, self.descriptor._compile_db_function(ctx)
            )
        else:
            compiled_descriptor = self.descriptor._compile_descriptor(ctx)

        if isinstance(self.value, CompilableDbFunction):
            compiled_db_function = cast(CompiledDbFunction, self.value._compile_db_function(ctx))
            compiled_parameter_template = compiled_db_function.full_template.format(
                variable_or_value=f"${compiled_db_function.inserted_parameter}"
            )

            return CompiledExpression(
                outer_template=compiled_descriptor.full_template,
                expression_template=self.template.format(
                    variable=compiled_descriptor.variable_path,
                    parameter=compiled_parameter_template,
                ),
                expression_variable=compiled_descriptor.variable,
                full_path=compiled_descriptor.full_path,
            )

        parameter_name = ctx.add_parameter(self.value)
        return CompiledExpression(
            outer_template=compiled_descriptor.full_template,
            expression_template=self.template.format(
                variable=compiled_descriptor.variable_path, parameter=f"${parameter_name}"
            ),
            expression_variable=compiled_descriptor.variable,
            full_path=compiled_descriptor.full_path,
        )

    def _compile_query(
        self, ctx: CompilationContext, precompiled: Optional[CompiledExpression] = None
    ) -> str:
        logger.debug("Compiling %s to query string", self.__class__.__name__)
        compiled = precompiled or self._compile_expression(ctx)
        return compiled.to_query_string()


@dataclass(frozen=True)
class InvertExpression(CompilableAndRunnableExpression):
    """A invert expression which can be compiled by a query builder."""

    expression: Union["CompoundExpression", CompilableAndRunnableExpression]

    def _compile_expression(self, ctx: CompilationContext) -> CompiledExpression:
        logger.debug("Compiling %s", self.__class__.__name__)
        if isinstance(self.expression, CompoundExpression):
            # `CompiledExpression` objects are only needed to be able to optimize in compound expressions
            # If we apply a NOT to a compound expression, no optimization is needed at this level and we can
            # compile the compound expression here directly
            compiled_query = self.expression._compile_query(ctx)
            return CompiledExpression(
                outer_template="{innermost_template}",
                expression_template="NOT({variable})",
                expression_variable=compiled_query,
                full_path=None,
            )

        compiled = self.expression._compile_expression(ctx)
        return CompiledExpression(
            outer_template=compiled.outer_template,
            expression_template=f"NOT({compiled.expression_template})",
            expression_variable=compiled.expression_variable,
            full_path=compiled.full_path,
        )

    def _compile_query(
        self, ctx: CompilationContext, precompiled: Optional[CompiledExpression] = None
    ) -> str:
        logger.debug("Compiling %s to query string", self.__class__.__name__)
        compiled = precompiled or self._compile_expression(ctx)
        return compiled.to_query_string()


@dataclass(frozen=True)
class CompoundExpression(RunnableExpression):
    """A compound expression which can be compiled by a query builder."""

    operator: LogicalExpressionTemplate
    expressions: List[Union["CompoundExpression", CompilableAndRunnableExpression]]

    def __and__(
        self, other: Union["CompoundExpression", CompilableAndRunnableExpression]
    ) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import and_

        if self.operator == LogicalExpressionTemplate.AND:
            return and_(*self.expressions, other)

        return and_(self, other)

    def __or__(
        self, other: Union["CompoundExpression", CompilableAndRunnableExpression]
    ) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import or_

        if self.operator == LogicalExpressionTemplate.OR:
            return or_(*self.expressions, other)

        return or_(self, other)

    def __xor__(
        self, other: Union["CompoundExpression", CompilableAndRunnableExpression]
    ) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import xor

        if self.operator == LogicalExpressionTemplate.XOR:
            return xor(*self.expressions, other)

        return xor(self, other)

    def __invert__(self) -> CompilableAndRunnableExpression:
        from loomi.query_api.functions.comparison import not_

        return not_(self)

    def _compile_query(
        self, ctx: CompilationContext, precompiled: Optional[CompiledExpression] = None
    ) -> str:
        logger.debug("Compiling %s to query string", self.__class__.__name__)

        query_strings: List[str] = []
        path_map: Dict[str, List[CompiledExpression]] = {}

        for expression in self.expressions:
            if isinstance(expression, CompoundExpression):
                query_strings.append(expression._compile_query(ctx))
                continue

            compiled_expression = expression._compile_expression(ctx)
            if compiled_expression.full_path is None:
                query_strings.append(expression._compile_query(ctx))
                continue

            path_map.setdefault(compiled_expression.full_path, [])
            path_map[compiled_expression.full_path].append(compiled_expression)

        # Optimize list queries by combining them in a single nested WHERE statement instead of
        # multiple individual ones
        for combinable_expressions in path_map.values():
            first_expression = combinable_expressions[0]

            if len(combinable_expressions) == 1:
                query_strings.append(first_expression.to_query_string())
                continue

            optimized_expression = CompiledExpression(
                outer_template=first_expression.outer_template,
                expression_template=f" {self.operator.value} ".join(
                    [expression.expression_template for expression in combinable_expressions]
                ),
                expression_variable=first_expression.expression_variable,
                full_path=first_expression.full_path,
            )
            query_strings.append(optimized_expression.to_query_string())

        return f" {self.operator.value} ".join(query_strings)


@dataclass(frozen=True)
class CustomCypherExpression(CompilableAndRunnableExpression):
    """A custom cypher expression which can be compiled by a query builder."""

    template: str
    model_map: Dict[str, QueryModelType]
    parameter_map: Dict[str, Any]

    def _compile_expression(self, ctx: CompilationContext) -> CompiledExpression:
        logger.debug("Compiling models defined for custom cypher expression")
        models_map = {
            placeholder: ctx.get_variable(model) for placeholder, model in self.model_map.items()
        }
        parameters_map = {
            placeholder: f"${ctx.add_parameter(parameter)}"
            for placeholder, parameter in self.parameter_map.items()
        }

        return CompiledExpression(
            outer_template="{innermost_template}",
            expression_template="{variable}",
            expression_variable=self.template.format(**models_map, **parameters_map),
            full_path=None,
        )

    def _compile_query(
        self, ctx: CompilationContext, precompiled: Optional[CompiledExpression] = None
    ) -> str:
        logger.debug("Compiling %s to query string", self.__class__.__name__)
        compiled = precompiled or self._compile_expression(ctx)
        return compiled.to_query_string()
