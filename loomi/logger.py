import logging
from typing import Optional

from typing_extensions import Literal


def get_logger(
    name: Optional[Literal["driver", "change_tracker", "model", "query_api"]] = None,
) -> logging.Logger:
    """
    Helper to get a namespaced logger under the 'loomi' namespace.

    Args:
        name (Optional[str]): Sub-logger name. Returns the namespace root logger if not
        defined. Defaults to `None`.

    Returns:
        logging.Logger: The namespaced logger.
    """
    if name is None:
        return logging.getLogger("loomi")

    return logging.getLogger(f"loomi.{name}")
