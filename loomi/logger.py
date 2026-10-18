import logging
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import Any, Mapping, Union

from typing_extensions import Literal

log_ctx: ContextVar[dict[str, Any]] = ContextVar("loomi_log_ctx", default={})


class LogContext(StrEnum):
    """Commonly used log context keys for Loomi ORM."""

    DRIVER = "driver"
    SERVER_TYPE = "server_type"
    SERVER_VERSION = "server_version"
    MODEL_NAME = "model_name"
    MODEL_HASH = "model_hash"
    CHANGE_TRACKER_OPERATION = "operation"
    CHANGE_TRACKER_FLUSH_SCOPE = "flush_scope"


class LogContextFilter(logging.Filter):
    """
    Optional logging filter for text formatters.

    Opt-in: Users of your library can explicitly add this to their handlers
    if they want context variables to be accessible via format strings like %(model_name)s.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in log_ctx.get().items():
            setattr(record, key, value)
        return True


@contextmanager
def _scoped_log_ctx(ctx: Mapping[Union[StrEnum, str], Any]):
    # Sanitize enum keys to plain strings
    sanitized_ctx = {str(k): v for k, v in ctx.items()}
    token = log_ctx.set({**log_ctx.get(), **sanitized_ctx})
    try:
        yield
    finally:
        log_ctx.reset(token)


def get_logger(name: Literal["driver", "change_tracker", "model", "query_api"]) -> logging.Logger:
    """
    Helper to get a namespaced logger under the 'loomi' namespace.

    Args:
        name (str): Sub-logger name.

    Returns:
        logging.Logger: The namespaced logger.
    """
    return logging.getLogger(f"loomi.{name}")
