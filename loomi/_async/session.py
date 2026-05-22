# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional, Union

import neo4j

from loomi._async.change_tracker import AsyncChangeTracker
from loomi._async.result import AsyncResult
from loomi._async.transaction import AsyncTransaction
from loomi._logger import logger

if TYPE_CHECKING:
    from loomi._async.client import AsyncClient

    _Base = neo4j.AsyncSession
else:
    AsyncClient = object
    _Base = object


class AsyncSession(_Base):
    """Wrapper for `neo4j.AsyncSession` allowing for additional functionality."""

    __session: neo4j.AsyncSession
    __client: AsyncClient
    __change_tracker: AsyncChangeTracker

    def __init__(self, session: neo4j.AsyncSession, client: AsyncClient):
        self.__session = session
        self.__client = client
        self.__change_tracker = AsyncChangeTracker(session, client)

    def __getattr__(self, name: str):
        return getattr(self.__session, name)

    async def __aenter__(self):
        await self.__session.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self.__session.__aexit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> AsyncChangeTracker:
        """
        Change tracker exposed by this session. Will be used when `tracking` is set to `true` in a
        query.
        """
        return self.__change_tracker

    async def run(
        self,
        query: Union[LiteralString, neo4j.Query],
        parameters: Optional[Dict[str, Any]] = None,
        tracking: bool = False,
        **kwargs: Any,
    ) -> AsyncResult:
        """
        Method providing the same interface as `neo4j.AsyncSession.run`, with some additional
        functionality. For more information on the native behavior, see `neo4j.AsyncSession.run`.

        Args:
            query (Union[LiteralString, Query]): See `neo4j.AsyncSession.run`.
            parameters (Optional[str, Any]): See `neo4j.AsyncSession.run`.
            tracking (bool): Whether results from this query should automatically be tracked
                in the `change tracker`. Defaults to `False`.
            kwargs: See `neo4j.AsyncSession.run`.

        Returns:
            Result: A wrapper for `neo4j.AsyncResult` objects.
        """
        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in dict(**parameters, **kwargs).items())
            if parameters is not None
            else ""
        )
        logging_query = query if isinstance(query, str) else query.text

        logger.info("Query: %s -- Parameters: [%s]", logging_query, logging_parameters)
        original_result = await self.__session.run(query, parameters, **kwargs)
        return AsyncResult(
            original_result, self.__client, self.__change_tracker if tracking else None
        )

    async def begin_transaction(
        self, metadata: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> AsyncTransaction:
        """
        Method providing the same interface as `neo4j.AsyncSession.begin_transaction`. If any entity
        is returned, it will be transformed to it's corresponding model.
        """
        original_transaction = await self.__session.begin_transaction(metadata, timeout)
        return AsyncTransaction(original_transaction, self.__client)
