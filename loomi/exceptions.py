class LoomiError(Exception):
    """Base Loomi error."""


class ModelInitializationError(LoomiError):
    """Error related to model initialization."""


class QueryCompileError(LoomiError):
    """Error related to compiling a query."""
