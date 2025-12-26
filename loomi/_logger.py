import logging
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import Any, Mapping, Union

log_ctx = ContextVar("loomi_log_ctx", default={})


class _LogContextKey(StrEnum):
    DRIVER = "loomi.driver"
    SERVER_TYPE = "loomi.server_type"


class _LogContextFilter(logging.Filter):
    def filter(self, record):
        for key, value in log_ctx.get().items():
            setattr(record, key, value)
        return True


@contextmanager
def _scoped_log_ctx(ctx: Mapping[Union[StrEnum, str], Any]):
    token = log_ctx.set({**log_ctx.get(), **ctx})
    try:
        yield
    finally:
        log_ctx.reset(token)


logger = logging.getLogger("loomi")
logger.addFilter(_LogContextFilter())
