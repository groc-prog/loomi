# pylint: disable=missing-function-docstring

from dataclasses import dataclass
from typing import Any, Dict, List, Union, cast

from loomi._core.types import QueryModelType
from loomi.exceptions import QueryError
from loomi.logger import get_logger
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableDescriptor,
    CompilableExpression,
    CompiledDescriptor,
    CompiledExpression,
    CompiledExpressionSide,
)
from loomi.query_api._core.templates import (
    ArithmeticExpressionTemplate,
    ExpressionTemplate,
    LogicalExpressionTemplate,
)

logger = get_logger("query_api")


@dataclass(frozen=True)
class ExpressionMixin:
    def __invert__(self) -> CompilableExpression:
        from loomi.query_api.functions.comparison import not_

        return not_(cast(CompilableExpression, self))

    def __and__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import and_

        return and_(cast(CompilableExpression, self), other)

    def __or__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import or_

        return or_(cast(CompilableExpression, self), other)

    def __xor__(self, other: "Expression") -> "CompoundExpression":
        from loomi.query_api.functions.comparison import xor

        return xor(cast(CompilableExpression, self), other)


@dataclass(frozen=True)
class Expression(ExpressionMixin, CompilableExpression):
    left: Union[CompilableDescriptor, CompilableDbFunction, Any]
    template: Union[ExpressionTemplate, ArithmeticExpressionTemplate]
    right: Union[CompilableDescriptor, CompilableDbFunction, CompilableExpression, Any]

    def __compile_side(
        self,
        ctx: CompilationContext,
        value: Union[CompilableDescriptor, CompilableDbFunction, CompilableExpression, Any],
    ) -> CompiledExpressionSide:
        if isinstance(value, CompilableExpression):
            logger.debug(
                "Expression side is a expression, compiling expression and transforming to final output"
            )
            compiled_expression = value._compile_expression(ctx)

            if compiled_expression.full_path is not None:
                raise QueryError(
                    "Invalid right side of expression passed. Expected primitive value, DB function, nested "
                    "expression or field descriptor without list path operators, but got "
                    f"{compiled_expression.full_path}"
                )

            # Expressions nested inside expressions are simply compiled to a expression side by wrapping
            # them in parenthesis
            return CompiledExpressionSide(
                outer_template="{innermost_template}",
                inner_template=f"({compiled_expression.to_query_string()})",
                expression_variable=None,
                full_path=None,
            )

        if isinstance(value, CompilableDescriptor):
            logger.debug(
                "Expression side is a field descriptor, compiling descriptor to final output"
            )
            compiled_descriptor = value._compile_descriptor(ctx)

            # Descriptors can be returned directly. The `expression_variable` is passed on, but
            # only the expression value of the left side of the expression will be included in the
            # final output
            return CompiledExpressionSide(
                outer_template=compiled_descriptor.full_template,
                inner_template=compiled_descriptor.variable_path.format(
                    variable=compiled_descriptor.variable
                ),
                expression_variable=compiled_descriptor.variable,
                full_path=compiled_descriptor.full_path,
            )

        if isinstance(value, CompilableDbFunction):
            logger.debug("Expression side is a DB function, compiling result")
            compiled_db_function_or_descriptor = value._compile_db_function(ctx)

            # We will get a descriptor with a modified template here if the DB function wraps a descriptor
            if isinstance(compiled_db_function_or_descriptor, CompiledDescriptor):
                logger.debug(
                    "Result of DB function compilation is a field descriptor, compiling descriptor to final output"
                )
                return CompiledExpressionSide(
                    outer_template=compiled_db_function_or_descriptor.full_template,
                    inner_template=compiled_db_function_or_descriptor.variable_path.format(
                        variable=compiled_db_function_or_descriptor.variable
                    ),
                    expression_variable=compiled_db_function_or_descriptor.variable,
                    full_path=compiled_db_function_or_descriptor.full_path,
                )

            logger.debug("Compiling expression side to final output")
            # If the DB function wraps a primitive value, we can compile the template directly
            return CompiledExpressionSide(
                outer_template="{innermost_template}",
                inner_template=compiled_db_function_or_descriptor.full_template.format(
                    variable_or_value=f"${compiled_db_function_or_descriptor.inserted_parameter}"
                ),
                expression_variable=None,
                full_path=None,
            )

        parameter_name = ctx.add_parameter(value)
        logger.debug(
            "Expression side is a primitive value. Final output for side is parameter %s",
            parameter_name,
        )

        # Primitive values can also be returned by simply compiling the template from the parameter
        # it was assigned
        return CompiledExpressionSide(
            outer_template="{innermost_template}",
            inner_template=f"${parameter_name}",
            expression_variable=None,
            full_path=None,
        )

    def _compile_expression(self, ctx: CompilationContext) -> CompiledExpression:
        logger.debug("Compiling expression for template %s", self.template.name)

        left = self.__compile_side(ctx, self.left)
        right = self.__compile_side(ctx, self.right)

        # We can not build expressions with nested list path operators on the right side
        # They are only allowed on the left side, which will put the actual expression somewhere
        # inside the list path
        if right.full_path is not None:
            raise QueryError(
                "Invalid right side of expression passed. Expected primitive value, DB function, nested expression "
                f"or field descriptor without list path operators, but got {right.full_path}"
            )

        return CompiledExpression(
            outer_template=left.outer_template,
            expression_template=self.template.format(
                left=left.inner_template, right=right.inner_template
            ),
            # Only the expression variable of the left side is passed on here since this will be
            # used when optimizing list path expressions in compound expressions
            expression_variable=left.expression_variable,
            full_path=left.full_path,
        )


@dataclass(frozen=True)
class InvertExpression(CompilableExpression):
    expression: Union["CompoundExpression", CompilableExpression]

    def _compile_expression(self, ctx: CompilationContext) -> CompiledExpression:
        logger.debug("Compiling %s", self.__class__.__name__)
        if isinstance(self.expression, CompoundExpression):
            # `CompiledExpression` objects are only needed to be able to optimize in compound expressions
            # If we apply a NOT to a compound expression, no optimization is needed at this level and we can
            # compile the compound expression here directly
            compiled_query = self.expression.to_query_string(ctx)
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


@dataclass(frozen=True)
class CompoundExpression:
    operator: LogicalExpressionTemplate
    expressions: List[Union["CompoundExpression", CompilableExpression]]

    def __and__(
        self, other: Union["CompoundExpression", CompilableExpression]
    ) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import and_

        if self.operator == LogicalExpressionTemplate.AND:
            return and_(*self.expressions, other)

        return and_(self, other)

    def __or__(
        self, other: Union["CompoundExpression", CompilableExpression]
    ) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import or_

        if self.operator == LogicalExpressionTemplate.OR:
            return or_(*self.expressions, other)

        return or_(self, other)

    def __xor__(
        self, other: Union["CompoundExpression", CompilableExpression]
    ) -> "CompoundExpression":
        from loomi.query_api.functions.comparison import xor

        if self.operator == LogicalExpressionTemplate.XOR:
            return xor(*self.expressions, other)

        return xor(self, other)

    def __invert__(self) -> CompilableExpression:
        from loomi.query_api.functions.comparison import not_

        return not_(self)

    def to_query_string(self, ctx: CompilationContext) -> str:
        """
        Generates a query string from the compound expression.

        Args:
            ctx (CompilationContext): The compilation context to use for generating the
            query string.

        Returns:
            str: The part of the query string represented by this compiled expression.
        """
        logger.debug(
            "Compiling %s with %d expressions to query string",
            self.__class__.__name__,
            len(self.expressions),
        )

        query_strings: List[str] = []
        path_map: Dict[str, List[CompiledExpression]] = {}

        for expression in self.expressions:
            if isinstance(expression, CompoundExpression):
                compiled_compound_expression = expression.to_query_string(ctx)

                if expression.operator != self.operator:
                    query_strings.append(f"({compiled_compound_expression})")
                else:
                    query_strings.append(compiled_compound_expression)

                continue

            compiled_expression = expression._compile_expression(ctx)
            if compiled_expression.full_path is None:
                query_strings.append(compiled_expression.to_query_string())
                continue

            path_map.setdefault(compiled_expression.full_path, [])
            path_map[compiled_expression.full_path].append(compiled_expression)

        # Optimize list queries by combining them in a single nested WHERE statement instead of
        # multiple individual ones
        logger.debug("Checking for possible query optimizations in %d paths", len(path_map.keys()))
        for path, combinable_expressions in path_map.items():
            first_expression = combinable_expressions[0]

            if len(combinable_expressions) == 1:
                query_strings.append(first_expression.to_query_string())
                continue

            logger.debug("Optimizing expression at path %s", path)
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
class CustomCypherExpression(CompilableExpression):
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
