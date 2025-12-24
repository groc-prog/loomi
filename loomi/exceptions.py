class LoomiError(Exception):
    """Base Loomi error."""


class NonHydratedModelError(LoomiError):
    """Error related to usage of non hydrated Loomi models."""


class EmptyGraphError(LoomiError):
    """Error related to the LoomiPath class."""
