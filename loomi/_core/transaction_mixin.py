import logging
from typing import Any, Dict, LiteralString, Optional

from loomi.logger import get_logger

logger = get_logger("driver")


class TransactionMixin:
    def _log_query(
        self, query: LiteralString, parameters: Optional[Dict[str, Any]] = None, **kwparameters: Any
    ) -> None:
        if not logger.isEnabledFor(logging.INFO):
            return

        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in {**parameters, **kwparameters}.items())
            if parameters is not None
            else ""
        )
        logger.info("Query: %s -- Parameters: [%s]", query, logging_parameters)
