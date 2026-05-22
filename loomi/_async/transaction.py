# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional

import neo4j

from loomi._async.change_tracker import AsyncChangeTracker
from loomi._async.result import AsyncResult
from loomi._logger import logger

if TYPE_CHECKING:
    from loomi._async.client import AsyncClient

    _Base = neo4j.AsyncTransaction
else:
    AsyncClient = object
    _Base = object


class AsyncTransaction(_Base):
    """Wrapper for `neo4j.AsyncTransaction` allowing for additional functionality."""

    __transaction: neo4j.AsyncTransaction
    __client: AsyncClient
    __change_tracker: AsyncChangeTracker

    def __init__(self, transaction: neo4j.AsyncTransaction, client: AsyncClient):
        self.__transaction = transaction
        self.__client = client
        self.__change_tracker = AsyncChangeTracker(transaction, client)

    def __getattr__(self, name: str):
        return getattr(self.__transaction, name)

    async def __aenter__(self):
        await self.__transaction.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self.__transaction.__aexit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> AsyncChangeTracker:
        """
        Change tracker exposed by this transaction. Will be used when `tracking` is set to `true`
        in a query.
        """
        return self.__change_tracker

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

        logger.info("Query: %s -- Parameters: [%s]", query, logging_parameters)
        original_result = await self.__transaction.run(query, parameters, **kwparameters)
        return AsyncResult(
            original_result, self.__client, self.__change_tracker if tracking else None
        )
