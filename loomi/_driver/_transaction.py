# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING

from neo4j import AsyncTransaction, Transaction

from loomi._driver._result import LoomiAsyncResult, LoomiResult

if TYPE_CHECKING:
    from loomi.client.async_client import LoomiAsyncClient
    from loomi.client.sync_client import LoomiClient
else:
    LoomiClient = object
    LoomiAsyncClient = object


class LoomiTransaction(Transaction):
    """
    Wrapper for `neo4j.Transaction` allowing for automatic transformation of entities returned by
    queries.
    """

    __transaction: Transaction
    __client: LoomiClient

    def __init__(self, transaction: Transaction, client: LoomiClient):
        self.__transaction = transaction
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__transaction, name)

    def __enter__(self):
        self.__transaction.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self.__transaction.__exit__(exception_type, exception_value, traceback)

    def run(self, *args, **kwargs):
        """
        Method providing the same interface as `neo4j.Transaction.run`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = self.__transaction.run(*args, **kwargs)
        return LoomiResult(original_result, self.__client)


class LoomiAsyncTransaction(AsyncTransaction):
    """
    Wrapper for `neo4j.AsyncTransaction` allowing for automatic transformation of entities returned
    by queries.
    """

    __transaction: AsyncTransaction
    __client: LoomiAsyncClient

    def __init__(self, transaction: AsyncTransaction, client: LoomiAsyncClient):
        self.__transaction = transaction
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__transaction, name)

    async def __aenter__(self):
        await self.__transaction.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self.__transaction.__aexit__(
            exception_type, exception_value, traceback
        )

    async def run(self, *args, **kwargs):
        """
        Method providing the same interface as `neo4j.AsyncTransaction.run`. If a entity is
        returned, it will be transformed to it's corresponding model.
        """
        original_result = await self.__transaction.run(*args, **kwargs)
        return LoomiAsyncResult(original_result, self.__client)
