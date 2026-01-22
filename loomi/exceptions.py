class LoomiError(Exception):
    """Base Loomi error."""


class ModelError(LoomiError):
    """Error related to models."""


class SerializationError(LoomiError):
    """Error related to model serialization."""


class ModelTrackingError(LoomiError):
    """Error related to the change tracker."""


class QueryError(LoomiError):
    """Error related to queries and query builders."""
