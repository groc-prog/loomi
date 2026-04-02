from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, cast, overload

from loomi.query._context import QueryCompilationContext
from loomi.query._protocols import CompilableDescriptor
from loomi.query._templates import DbFunctionTemplate


@dataclass(frozen=True)
class CompiledTransformer:
    """The compiled version for a given transformer."""

    template: str
    transformed_path: str


@dataclass(frozen=True)
class DbFunctionTransformer:
    """Descriptor class used to apply DB functions to fields/parameters."""

    to_transform: Any
    template: Union[DbFunctionTemplate, str]
    args: List[Any]

    @overload
    def _compile(self, ctx: QueryCompilationContext) -> CompiledTransformer: ...

    @overload
    def _compile(
        self, ctx: QueryCompilationContext, expression_template: str, value: Optional[Any]
    ) -> CompiledTransformer: ...

    def _compile(
        self,
        ctx: QueryCompilationContext,
        expression_template: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> CompiledTransformer:
        template_to_compile = (
            self.template.value if isinstance(self.template, DbFunctionTemplate) else self.template
        )

        parameter_map: Dict[str, str] = {}
        for index, arg in enumerate(self.args):
            parameter_name = ctx.add_parameter(arg)
            parameter_map[f"arg{index}"] = f"${parameter_name}"

        # If we are dealing with another DB function, we can compile the template directly
        # We have to check for DbFunctionTransformer here first, since it shares the same signature
        # for the _compile method as CompilableDescriptor
        if isinstance(self.to_transform, DbFunctionTransformer):
            compiled = self.to_transform._compile(ctx, cast(str, expression_template), value)
            db_function_template = template_to_compile.format(
                variable_or_parameter="{transformed}", **parameter_map
            )
            return CompiledTransformer(
                compiled.template.format(transformed=db_function_template),
                compiled.transformed_path,
            )

        # If we are not dealing with a descriptor, we can compile the template with the
        # parameter name directly
        if isinstance(self.to_transform, CompilableDescriptor):
            compiled = self.to_transform._compile(ctx, cast(str, expression_template), value)
            descriptor_template = compiled.template.format(
                path=template_to_compile.format(
                    variable_or_parameter="{transformed}", **parameter_map
                ),
                parameter=compiled.parameter_name,
            )
            return CompiledTransformer(
                descriptor_template,
                compiled.variable_path,
            )

        parameter_name = ctx.add_parameter(self.to_transform)
        return CompiledTransformer(
            template_to_compile.format(variable_or_parameter="{transformed}", **parameter_map),
            f"${parameter_name}",
        )
