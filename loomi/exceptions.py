class LoomiError(Exception):
    """Base Loomi error."""


class ModelInitializationError(LoomiError):
    """Error related to model initialization."""


class QueryCompileError(LoomiError):
    """Error related to compiling a query."""


class PropertyAccessorError(LoomiError):
    """Error related to property accessors on a model."""
