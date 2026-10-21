import logging

from typing_extensions import Literal


def get_logger(name: Literal["driver", "change_tracker", "model", "query_api"]) -> logging.Logger:
    """
    Helper to get a namespaced logger under the 'loomi' namespace.

    Args:
        name (str): Sub-logger name.

    Returns:
        logging.Logger: The namespaced logger.
    """
    return logging.getLogger(f"loomi.{name}")
