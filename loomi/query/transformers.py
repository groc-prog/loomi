from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast, overload

from loomi.query._context import QueryCompilationContext
from loomi.query._templates import DbFunctionTemplate


@dataclass(frozen=True)
class DbFunctionTransformer:
    """Descriptor class used to apply DB functions to fields/parameters."""

    descriptor_or_parameter_value: Any
    template: DbFunctionTemplate
    args: List[Any] = []

    @overload
    def _compile(self, ctx: QueryCompilationContext) -> str: ...

    @overload
    def _compile(
        self, ctx: QueryCompilationContext, expression_template: str, value: Optional[Any]
    ) -> str: ...

    def _compile(
        self,
        ctx: QueryCompilationContext,
        expression_template: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> str:
        from loomi.query.descriptor import FieldDescriptor

        parameter_map: Dict[str, str] = {}
        for index, arg in enumerate(self.args):
            parameter_name = ctx.add_parameter(arg)
            parameter_map[f"arg{index}"] = parameter_name

        # If we are not dealing with a descriptor, we can compile the template with the
        # parameter name directly
        if not isinstance(self.descriptor_or_parameter_value, FieldDescriptor):
            parameter_name = ctx.add_parameter(self.descriptor_or_parameter_value)
            return self.template.format(variable_or_parameter=f"${parameter_name}", **parameter_map)

        compiled = self.descriptor_or_parameter_value._compile(
            ctx, cast(str, expression_template), value
        )
        compiled_db_fn = self.template.format(
            variable_or_parameter=compiled.variable_path, **parameter_map
        )
        return compiled.template.format(path=compiled_db_fn, parameter=compiled.parameter_name)
