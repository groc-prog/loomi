from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from loomi._logger import logger
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableDescriptor,
    CompiledDbFunction,
)
from loomi.query_api._core.templates import DbFunctionTemplate

if TYPE_CHECKING:
    from loomi.query_api._core.context import CompilationContext
else:
    CompilationContext = object


@dataclass(frozen=True)
class DbFunction(CompilableDbFunction):
    """Class used to apply DB functions to fields/parameters."""

    to_wrap: Any
    template: Union[DbFunctionTemplate, str]
    args: List[Any]

    def _compile_db_function(
        self,
        ctx: CompilationContext,
        expression_template: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> CompiledDbFunction:
        logger.debug("Compiling DB function. Template: %s", expression_template)

        template_to_compile = (
            self.template.value if isinstance(self.template, DbFunctionTemplate) else self.template
        )

        parameter_map: Dict[str, str] = {}
        for index, arg in enumerate(self.args):
            parameter_name = ctx.add_parameter(arg)
            parameter_map[f"arg{index}"] = f"${parameter_name}"

        # If we are dealing with another DB function, we can compile the template directly
        if isinstance(self.to_wrap, CompilableDbFunction):
            compiled = self.to_wrap._compile_db_function(ctx, cast(str, expression_template), value)
            db_function_template = template_to_compile.format(
                variable_or_parameter="{wrapped}", **parameter_map
            )
            return CompiledDbFunction(
                compiled.template.format(wrapped=db_function_template),
                compiled.wrapped_path,
            )

        # If we are not dealing with a descriptor, we can compile the template with the
        # parameter name directly
        if isinstance(self.to_wrap, CompilableDescriptor):
            compiled = self.to_wrap._compile_descriptor(ctx, cast(str, expression_template), value)
            descriptor_template = compiled.template.format(
                path=template_to_compile.format(variable_or_parameter="{wrapped}", **parameter_map),
                parameter=compiled.parameter_name,
            )
            return CompiledDbFunction(
                descriptor_template,
                compiled.variable_path,
            )

        parameter_name = ctx.add_parameter(self.to_wrap)
        return CompiledDbFunction(
            template_to_compile.format(variable_or_parameter="{wrapped}", **parameter_map),
            f"${parameter_name}",
        )
