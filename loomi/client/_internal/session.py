# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Union

import neo4j

from loomi._logger import _logger
from loomi.client._internal._change_tracker import AsyncChangeTracker, ChangeTracker
from loomi.client._internal.result import AsyncResult, Result
from loomi.client._internal.transaction import AsyncTransaction, Transaction

if TYPE_CHECKING:
    from loomi.client.async_client import AsyncClient
    from loomi.client.sync_client import Client

    _Base = neo4j.Session
    _AsyncBase = neo4j.AsyncSession
else:
    Client = object
    AsyncClient = object

    _Base = object
    _AsyncBase = object


class Session(_Base):
    """Wrapper for `neo4j.Session` allowing for additional functionality."""

    _session: neo4j.Session
    _client: Client
    _change_tracker: ChangeTracker

    def __init__(self, session: neo4j.Session, client: Client):
        self._session = session
        self._client = client
        self._change_tracker = ChangeTracker(session, client)

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    def __enter__(self):
        self._session.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self._session.__exit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> ChangeTracker:
        """
        Change tracker exposed by this session. Will be used when `tracking` is set to `true` in a
        query.
        """
        return self._change_tracker

    def run(
        self,
        query: Union[LiteralString, neo4j.Query],
        parameters: Dict[str, Any] | None = None,
        tracking: bool = False,
        **kwargs: Any,
    ) -> Result:
        """
        Method providing the same interface as `neo4j.Session.run`, with some additional
        functionality. For more information on the native behavior, see `neo4j.Session.run`.

        Args:
            query (Union[LiteralString, Query]): See `neo4j.Session.run`.
            parameters (Optional[str, Any]): See `neo4j.Session.run`.
            tracking (bool): Whether results from this query should automatically be tracked
                in the `change tracker`. Defaults to `False`.
            kwargs: See `neo4j.Session.run`.

        Returns:
            Result: A wrapper for `neo4j.Result` objects.
        """
        logging_parameters = (
            ", ".join(f"{key}={value}" for key, value in {**parameters, **kwargs}.items())
            if parameters is not None
            else ""
        )
        logging_query = query if isinstance(query, str) else query.text

        _logger.info("Query: %s -- Parameters: [%s]", logging_query, logging_parameters)
        original_result = self._session.run(query, parameters, **kwargs)
        return Result(original_result, self._client, self._change_tracker if tracking else None)

    def begin_transaction(
        self, metadata: Dict[str, Any] | None = None, timeout: float | None = None
    ) -> Transaction:
        """
        Method providing the same interface as `neo4j.Session.begin_transaction`. If any entity
        is returned, it will be transformed to it's corresponding model.
        """
        original_transaction = self._session.begin_transaction(metadata, timeout)
        return Transaction(original_transaction, self._client)


class AsyncSession(_AsyncBase):
    """Wrapper for `neo4j.AsyncSession` allowing for additional functionality."""

    _session: neo4j.AsyncSession
    _client: AsyncClient
    _change_tracker: AsyncChangeTracker

    def __init__(self, session: neo4j.AsyncSession, client: AsyncClient):
        self._session = session
        self._client = client
        self._change_tracker = AsyncChangeTracker(session, client)

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    async def __aenter__(self):
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self._session.__aexit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> AsyncChangeTracker:
        """
        Change tracker exposed by this session. Will be used when `tracking` is set to `true` in a
        query.
        """
        return self._change_tracker

    async def run(
        self,
        query: Union[LiteralString, neo4j.Query],
        parameters: Dict[str, Any] | None = None,
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

        _logger.info("Query: %s -- Parameters: [%s]", logging_query, logging_parameters)
        original_result = await self._session.run(query, parameters, **kwargs)
        return AsyncResult(
            original_result, self._client, self._change_tracker if tracking else None
        )

    async def begin_transaction(
        self, metadata: Dict[str, Any] | None = None, timeout: float | None = None
    ) -> AsyncTransaction:
        """
        Method providing the same interface as `neo4j.AsyncSession.begin_transaction`. If any entity
        is returned, it will be transformed to it's corresponding model.
        """
        original_transaction = await self._session.begin_transaction(metadata, timeout)
        return AsyncTransaction(original_transaction, self._client)
