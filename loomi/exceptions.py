class LoomiError(Exception):
    """Base Loomi error."""


class ModelInitializationError(LoomiError):
    """Error related to model initialization."""


class ModelTrackingError(LoomiError):
    """Error related to the change tracker."""


class QueryError(LoomiError):
    """Error related to queries and query builders."""
