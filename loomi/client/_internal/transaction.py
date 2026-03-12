# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional

import neo4j

from loomi._logger import _logger
from loomi.client._internal._change_tracker import AsyncChangeTracker, ChangeTracker
from loomi.client._internal.result import AsyncResult, Result

if TYPE_CHECKING:
    from loomi.client.async_client import AsyncClient
    from loomi.client.sync_client import Client

    _Base = neo4j.Transaction
    _AsyncBase = neo4j.AsyncTransaction
else:
    Client = object
    AsyncClient = object

    _Base = object
    _AsyncBase = object


class Transaction(_Base):
    """Wrapper for `neo4j.Transaction` allowing for additional functionality."""

    _transaction: neo4j.Transaction
    _client: Client
    _change_tracker: ChangeTracker

    def __init__(self, transaction: neo4j.Transaction, client: Client):
        self._transaction = transaction
        self._client = client
        self._change_tracker = ChangeTracker(transaction, client)

    def __getattr__(self, name: str):
        return getattr(self._transaction, name)

    def __enter__(self):
        self._transaction.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self._transaction.__exit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> ChangeTracker:
        """
        Change tracker exposed by this transaction. Will be used when `tracking` is set to `true`
        in a query.
        """
        return self._change_tracker

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
        original_result = self._transaction.run(query, parameters, **kwparameters)
        return Result(original_result, self._client, self._change_tracker if tracking else None)


class AsyncTransaction(_AsyncBase):
    """Wrapper for `neo4j.AsyncTransaction` allowing for additional functionality."""

    _transaction: neo4j.AsyncTransaction
    _client: AsyncClient
    _change_tracker: AsyncChangeTracker

    def __init__(self, transaction: neo4j.AsyncTransaction, client: AsyncClient):
        self._transaction = transaction
        self._client = client
        self._change_tracker = AsyncChangeTracker(transaction, client)

    def __getattr__(self, name: str):
        return getattr(self._transaction, name)

    async def __aenter__(self):
        await self._transaction.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self._transaction.__aexit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> AsyncChangeTracker:
        """
        Change tracker exposed by this transaction. Will be used when `tracking` is set to `true`
        in a query.
        """
        return self._change_tracker

    async def run(
        self,
        query: LiteralString,
        parameters: Optional[Dict[str, Any]] = None,
        tracking: bool = False,
        **kwparameters: Any,
    ):
        """
        Method providing the same interface as `neo4j.AsyncTransaction.run`, with some additional
        functionality. For more information on the native behavior, see
        `neo4j.AsyncTransaction.run`.

        Args:
            query (Union[LiteralString, Query]): See `neo4j.AsyncTransaction.run`.
            parameters (Optional[str, Any]): See `neo4j.AsyncTransaction.run`.
            tracking (bool): Whether results from this query should automatically be tracked
                in the `change tracker`. Defaults to `False`.
            kwparameters: See `neo4j.AsyncTransaction.run`.

        Returns:
            Result: A wrapper for `neo4j.AsyncResult` objects.
        """
        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in dict(**parameters, **kwparameters).items())
            if parameters is not None
            else ""
        )

        _logger.info("Query: %s -- Parameters: [%s]", query, logging_parameters)
        original_result = await self._transaction.run(query, parameters, **kwparameters)
        return AsyncResult(
            original_result, self._client, self._change_tracker if tracking else None
        )
