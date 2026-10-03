from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi._logger import logger
from loomi.query_api._core.protocols import (
    CompilableDbFunction,
    CompilableDescriptor,
    CompiledDbFunction,
    CompiledDescriptor,
)
from loomi.query_api._core.templates import DbFunctionTemplate

if TYPE_CHECKING:
    from loomi.query_api._core.context import CompilationContext
else:
    CompilationContext = object


@dataclass(frozen=True)
class DbFunction(CompilableDbFunction):
    """Class used to apply DB functions to fields/parameters."""

    wrapped: Any
    template: Union[DbFunctionTemplate, str]
    args: List[Any]

    def _compile_db_function(
        self, ctx: CompilationContext
    ) -> Union[CompiledDescriptor, CompiledDbFunction]:
        logger.debug("Compiling DB function")
        template_to_compile = (
            self.template.value if isinstance(self.template, DbFunctionTemplate) else self.template
        )

        parameter_map: Dict[str, str] = {}
        for index, arg in enumerate(self.args):
            parameter_name = ctx.add_parameter(arg)
            parameter_map[f"arg{index}"] = f"${parameter_name}"

        # The thing to wrap is a descriptor, so we need to compile it and modify it's full template
        # to include the DB function
        if isinstance(self.wrapped, CompilableDescriptor):
            compiled_descriptor = self.wrapped._compile_descriptor(ctx)
            compiled_variable_path = template_to_compile.format(
                variable_or_parameter=compiled_descriptor.variable_path
            )

            return CompiledDescriptor(
                full_template=compiled_descriptor.full_template,
                variable_path=compiled_variable_path,
                variable=compiled_descriptor.variable,
                full_path=compiled_descriptor.full_path,
            )

        # The DB function is deeply nested, so we need to compile it and return
        # This can either return another DB function or a descriptor
        if isinstance(self.wrapped, CompilableDbFunction):
            compiled_db_function_or_descriptor = self.wrapped._compile_db_function(ctx)

            if isinstance(compiled_db_function_or_descriptor, CompiledDescriptor):
                compiled_variable_path = template_to_compile.format(
                    variable_or_parameter=compiled_db_function_or_descriptor.variable_path
                )

                return CompiledDescriptor(
                    full_template=compiled_db_function_or_descriptor.full_template,
                    variable_path=compiled_variable_path,
                    variable=compiled_db_function_or_descriptor.variable,
                    full_path=compiled_db_function_or_descriptor.full_path,
                )

            compiled_template = template_to_compile.format(
                variable_or_parameter="{variable_or_value}", **parameter_map
            )
            return CompiledDbFunction(
                full_template=compiled_db_function_or_descriptor.full_template.format(
                    variable_or_value=compiled_template
                ),
                inserted_parameter=compiled_db_function_or_descriptor.inserted_parameter,
            )

        # The DB function wraps a primitive value
        parameter_name = ctx.add_parameter(self.wrapped)
        return CompiledDbFunction(
            full_template=template_to_compile.format(
                variable_or_parameter="{variable_or_value}", **parameter_map
            ),
            inserted_parameter=parameter_name,
        )
