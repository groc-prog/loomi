class LoomiError(Exception):
    """Base Loomi error."""


class ModelInitializationError(LoomiError):
    """Error related to model initialization."""


class ClientError(LoomiError):
    """Error related to the Loomi client class."""
