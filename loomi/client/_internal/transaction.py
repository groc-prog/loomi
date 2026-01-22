# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional

from neo4j import AsyncTransaction, Transaction

from loomi._logger import _logger
from loomi.client._internal._change_tracker import AsyncChangeTracker, ChangeTracker
from loomi.client._internal.result import LoomiAsyncResult, LoomiResult

if TYPE_CHECKING:
    from loomi.client.async_client import LoomiAsyncClient
    from loomi.client.sync_client import LoomiClient

    _Base = Transaction
    _AsyncBase = AsyncTransaction
else:
    LoomiClient = object
    LoomiAsyncClient = object

    _Base = object
    _AsyncBase = object


class LoomiTransaction(_Base):
    """
    Wrapper for `neo4j.Transaction` allowing for automatic transformation of entities returned by
    queries.
    """

    _transaction: Transaction
    _client: LoomiClient
    _change_tracker: ChangeTracker

    def __init__(self, transaction: Transaction, client: LoomiClient):
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
        The change tracker specific to this transaction.
        """
        return self._change_tracker

    def run(
        self,
        query: LiteralString,
        parameters: Optional[Dict[str, Any]] = None,
        **kwparameters: Any,
    ):
        """
        Method providing the same interface as `neo4j.Transaction.run`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in dict(**parameters, **kwparameters).items())
            if parameters is not None
            else ""
        )

        _logger.info("Query: %s -- Parameters: [%s]", query, logging_parameters)
        original_result = self._transaction.run(query, parameters, **kwparameters)
        return LoomiResult(original_result, self._client)


class LoomiAsyncTransaction(_AsyncBase):
    """
    Wrapper for `neo4j.AsyncTransaction` allowing for automatic transformation of entities returned
    by queries.
    """

    _transaction: AsyncTransaction
    _client: LoomiAsyncClient
    _change_tracker: AsyncChangeTracker

    def __init__(self, transaction: AsyncTransaction, client: LoomiAsyncClient):
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
        The change tracker specific to this transaction.
        """
        return self._change_tracker

    async def run(
        self,
        query: LiteralString,
        parameters: Optional[Dict[str, Any]] = None,
        **kwparameters: Any,
    ):
        """
        Method providing the same interface as `neo4j.AsyncTransaction.run`. If a entity is
        returned, it will be transformed to it's corresponding model.
        """
        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in dict(**parameters, **kwparameters).items())
            if parameters is not None
            else ""
        )

        _logger.info("Query: %s -- Parameters: [%s]", query, logging_parameters)
        original_result = await self._transaction.run(query, parameters, **kwparameters)
        return LoomiAsyncResult(original_result, self._client)
