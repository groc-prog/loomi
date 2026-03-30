import logging
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import Any, Mapping, Union

log_ctx = ContextVar("loomi_log_ctx", default={})


class LogContextKey(StrEnum):
    """Commonly used log context variables."""

    DRIVER = "loomi.driver"
    SERVER_TYPE = "loomi.server_type"
    MODEL_NAME = "loomi.model.name"
    MODEL_IDENTIFIER = "loomi.model.identifier"
    CHANGE_TRACKER_OPERATION = "loomi.change_tracker.operation"
    CHANGE_TRACKER_FLUSH_SCOPE = "loomi.change_tracker.scope"


class LogContextFilter(logging.Filter):
    """Logging filter for adding context to the log record."""

    def filter(self, record):
        for key, value in log_ctx.get().items():
            setattr(record, key, value)
        return True


@contextmanager
def scoped_log_ctx(ctx: Mapping[Union[StrEnum, str], Any]):
    """
    Used to define a log scope with additional context.

    Args:
        ctx (Mapping[Union[StrEnum, str], Any]): The added context.
    """

    token = log_ctx.set({**log_ctx.get(), **ctx})
    try:
        yield
    finally:
        log_ctx.reset(token)


logger = logging.getLogger("loomi")
logger.addFilter(LogContextFilter())
