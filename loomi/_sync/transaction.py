# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional

import neo4j

from loomi._logger import _logger
from loomi._sync.change_tracker import ChangeTracker
from loomi._sync.result import Result

if TYPE_CHECKING:
    from loomi._sync.client import Client

    _Base = neo4j.Transaction
else:
    Client = object
    _Base = object


class Transaction(_Base):
    """Wrapper for `neo4j.Transaction` allowing for additional functionality."""

    __transaction: neo4j.Transaction
    __client: Client
    __change_tracker: ChangeTracker

    def __init__(self, transaction: neo4j.Transaction, client: Client):
        self.__transaction = transaction
        self.__client = client
        self.__change_tracker = ChangeTracker(transaction, client)

    def __getattr__(self, name: str):
        return getattr(self.__transaction, name)

    def __enter__(self):
        self.__transaction.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self.__transaction.__exit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> ChangeTracker:
        """
        Change tracker exposed by this transaction. Will be used when `tracking` is set to `true`
        in a query.
        """
        return self.__change_tracker

    def run(
        self,
        query: LiteralString,
        parameters: Optional[Dict[str, Any]] = None,
        tracking: bool = False,
        **kwparameters: Any,
    ):
        """
        Method providing the same interface as `neo4j.Transaction.run`, with some additional
        functionality. For more information on the native behavior, see `neo4j.Transaction.run`.

        Args:
            query (Union[LiteralString, Query]): See `neo4j.Transaction.run`.
            parameters (Optional[str, Any]): See `neo4j.Transaction.run`.
            tracking (bool): Whether results from this query should automatically be tracked
                in the `change tracker`. Defaults to `False`.
            kwparameters: See `neo4j.Transaction.run`.

        Returns:
            Result: A wrapper for `neo4j.Result` objects.
        """
        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in dict(**parameters, **kwparameters).items())
            if parameters is not None
            else ""
        )

        _logger.info("Query: %s -- Parameters: [%s]", query, logging_parameters)
        original_result = self.__transaction.run(query, parameters, **kwparameters)
        return Result(original_result, self.__client, self.__change_tracker if tracking else None)
