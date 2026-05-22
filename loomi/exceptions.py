class LoomiError(Exception):
    """Base Loomi error."""


class ClientError(LoomiError):
    """Error related to clients."""


class ModelError(LoomiError):
    """Error related to models."""


class SerializationError(LoomiError):
    """Error related to model serialization."""


class ChangeTrackerError(LoomiError):
    """Error related to the change tracker."""


class QueryError(LoomiError):
    """Error related to queries and query builders."""


class MigrationError(LoomiError):
    """Error related to migrations."""
