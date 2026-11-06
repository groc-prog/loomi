import logging
from typing import Any, Dict, LiteralString, Optional, Union

import neo4j

from loomi.logger import get_logger

logger = get_logger("driver")


class SessionMixin:
    def _log_query(
        self,
        query: Union[LiteralString, neo4j.Query],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        if not logger.isEnabledFor(logging.INFO):
            return

        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in {**parameters, **kwargs}.items())
            if parameters is not None
            else ""
        )
        logging_query = query if isinstance(query, str) else query.text
        logger.info("Query: %s -- Parameters: [%s]", logging_query, logging_parameters)
