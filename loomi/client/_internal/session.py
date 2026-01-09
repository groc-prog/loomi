# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Union

from neo4j import AsyncSession, Query, Session

from loomi.client._internal.result import LoomiAsyncResult, LoomiResult
from loomi.client._internal.transaction import LoomiAsyncTransaction, LoomiTransaction

if TYPE_CHECKING:
    from loomi.client.async_client import LoomiAsyncClient
    from loomi.client.sync_client import LoomiClient

    _Base = Session
    _AsyncBase = AsyncSession
else:
    LoomiClient = object
    LoomiAsyncClient = object

    _Base = object
    _AsyncBase = object


class LoomiSession(_Base):
    """
    Wrapper for `neo4j.Session` allowing for automatic transformation of entities returned by
    queries.
    """

    _session: Session
    _client: LoomiClient

    def __init__(self, session: Session, client: LoomiClient):
        self._session = session
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    def __enter__(self):
        self._session.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self._session.__exit__(exception_type, exception_value, traceback)

    def run(
        self,
        query: Union[LiteralString, Query],
        parameters: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LoomiResult:
        """
        Method providing the same interface as `neo4j.Session.run`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = self._session.run(query, parameters, **kwargs)
        return LoomiResult(original_result, self._client)

    def begin_transaction(
        self, metadata: Dict[str, Any] | None = None, timeout: float | None = None
    ) -> LoomiTransaction:
        """
        Method providing the same interface as `neo4j.Session.begin_transaction`. If a entity is
        returned, it will be transformed to it's corresponding model.
        """
        original_transaction = self._session.begin_transaction(metadata, timeout)
        return LoomiTransaction(original_transaction, self._client)


class LoomiAsyncSession(_AsyncBase):
    """
    Wrapper for `neo4j.AsyncSession` allowing for automatic transformation of entities returned by
    queries.
    """

    _session: AsyncSession
    _client: LoomiAsyncClient

    def __init__(self, session: AsyncSession, client: LoomiAsyncClient):
        self._session = session
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._session, name)

    async def __aenter__(self):
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self._session.__aexit__(exception_type, exception_value, traceback)

    async def run(
        self,
        query: Union[LiteralString, Query],
        parameters: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LoomiAsyncResult:
        """
        Method providing the same interface as `neo4j.AsyncSession.run`. If a entity is returned,
        it will be transformed to it's corresponding model.
        """
        original_result = await self._session.run(query, parameters, **kwargs)
        return LoomiAsyncResult(original_result, self._client)

    async def begin_transaction(
        self, metadata: Dict[str, Any] | None = None, timeout: float | None = None
    ) -> LoomiAsyncTransaction:
        """
        Method providing the same interface as `neo4j.AsyncSession.begin_transaction`. If a entity is
        returned, it will be transformed to it's corresponding model.
        """
        original_transaction = await self._session.begin_transaction(metadata, timeout)
        return LoomiAsyncTransaction(original_transaction, self._client)
