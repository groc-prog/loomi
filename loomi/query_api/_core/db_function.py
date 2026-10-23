from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union

from loomi.logger import get_logger
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


logger = get_logger("query_api")


@dataclass(frozen=True)
class DbFunction(CompilableDbFunction):
    wrapped: Any
    template: Union[DbFunctionTemplate, str]
    args: List[Any]

    def _compile_db_function(
        self, ctx: CompilationContext
    ) -> Union[CompiledDescriptor, CompiledDbFunction]:
        template_to_compile = (
            self.template.value if isinstance(self.template, DbFunctionTemplate) else self.template
        )
        logger.debug("Compiling DB function with template %s", template_to_compile)

        parameter_map: Dict[str, str] = {}
        for index, arg in enumerate(self.args):
            parameter_name = ctx.add_parameter(arg)
            parameter_map[f"arg{index}"] = f"${parameter_name}"

        logger.debug("Build parameter map for %d values", len(parameter_map.keys()))

        # The thing to wrap is a descriptor, so we need to compile it and modify it's full template
        # to include the DB function
        if isinstance(self.wrapped, CompilableDescriptor):
            compiled_descriptor = self.wrapped._compile_descriptor(ctx)
            compiled_variable_path = template_to_compile.format(
                variable_or_parameter=compiled_descriptor.variable_path, **parameter_map
            )

            return CompiledDescriptor(
                full_template=compiled_descriptor.full_template,
                variable_path=compiled_variable_path,
                variable=compiled_descriptor.variable,
                full_path=compiled_descriptor.full_path,
            )

        # The DB function is deeply nested, so we need to compile it and return
        # This can either return another DB function (in case the value of the DB function is a
        # primitive) or a descriptor (in case the value of the DB function is a descriptor) with a
        # modified template
        if isinstance(self.wrapped, CompilableDbFunction):
            logger.debug("Wrapped value is a DB function, compiling nested DB functions first")
            compiled_db_function_or_descriptor = self.wrapped._compile_db_function(ctx)

            if isinstance(compiled_db_function_or_descriptor, CompiledDescriptor):
                compiled_variable_path = template_to_compile.format(
                    variable_or_parameter=compiled_db_function_or_descriptor.variable_path,
                    **parameter_map,
                )

                logger.debug("Compiled DB function resolved to a descriptor")
                return CompiledDescriptor(
                    full_template=compiled_db_function_or_descriptor.full_template,
                    variable_path=compiled_variable_path,
                    variable=compiled_db_function_or_descriptor.variable,
                    full_path=compiled_db_function_or_descriptor.full_path,
                )

            logger.debug("Compiled DB function resolved to another DB function")
            compiled_template = compiled_db_function_or_descriptor.full_template.format(
                variable_or_value="{variable_or_value}"
            )
            return CompiledDbFunction(
                full_template=template_to_compile.format(
                    variable_or_parameter=compiled_template, **parameter_map
                ),
                inserted_parameter=compiled_db_function_or_descriptor.inserted_parameter,
            )

        # The DB function wraps a primitive value, we can build the correct template directly
        parameter_name = ctx.add_parameter(self.wrapped)

        logger.debug(
            "Compiled DB function is wrapping a primitive value with parameter %s", parameter_name
        )
        return CompiledDbFunction(
            full_template=template_to_compile.format(
                variable_or_parameter="{variable_or_value}", **parameter_map
            ),
            inserted_parameter=parameter_name,
        )
