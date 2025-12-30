# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional

from neo4j import AsyncTransaction, Transaction

from loomi._driver._result import LoomiAsyncResult, LoomiResult

if TYPE_CHECKING:
    from loomi.clients.async_client import LoomiAsyncClient
    from loomi.clients.sync_client import LoomiClient
else:
    LoomiClient = object
    LoomiAsyncClient = object


class LoomiTransaction(Transaction):
    """
    Wrapper for `neo4j.Transaction` allowing for automatic transformation of entities returned by
    queries.
    """

    _transaction: Transaction
    _client: LoomiClient

    def __init__(self, transaction: Transaction, client: LoomiClient):
        self._transaction = transaction
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._transaction, name)

    def __enter__(self):
        self._transaction.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self._transaction.__exit__(exception_type, exception_value, traceback)

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
        original_result = self._transaction.run(query, parameters, **kwparameters)
        return LoomiResult(original_result, self._client)


class LoomiAsyncTransaction(AsyncTransaction):
    """
    Wrapper for `neo4j.AsyncTransaction` allowing for automatic transformation of entities returned
    by queries.
    """

    _transaction: AsyncTransaction
    _client: LoomiAsyncClient

    def __init__(self, transaction: AsyncTransaction, client: LoomiAsyncClient):
        self._transaction = transaction
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._transaction, name)

    async def __aenter__(self):
        await self._transaction.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self._transaction.__aexit__(exception_type, exception_value, traceback)

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
        original_result = await self._transaction.run(query, parameters, **kwparameters)
        return LoomiAsyncResult(original_result, self._client)
