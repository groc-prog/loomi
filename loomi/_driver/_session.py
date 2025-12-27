# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Union

from neo4j import AsyncSession, Query, Session

from loomi._driver._result import LoomiAsyncResult, LoomiResult
from loomi._driver._transaction import LoomiAsyncTransaction, LoomiTransaction

if TYPE_CHECKING:
    from loomi.client.async_client import LoomiAsyncClient
    from loomi.client.sync_client import LoomiClient
else:
    LoomiClient = object
    LoomiAsyncClient = object


class LoomiSession(Session):
    """
    Wrapper for `neo4j.Session` allowing for automatic transformation of entities returned by
    queries.
    """

    __session: Session
    __client: LoomiClient

    def __init__(self, session: Session, client: LoomiClient):
        self.__session = session
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__session, name)

    def __enter__(self):
        self.__session.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self.__session.__exit__(exception_type, exception_value, traceback)

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
        original_result = self.__session.run(query, parameters, **kwargs)
        return LoomiResult(original_result, self.__client)

    def begin_transaction(
        self, metadata: Dict[str, Any] | None = None, timeout: float | None = None
    ) -> LoomiTransaction:
        """
        Method providing the same interface as `neo4j.Session.begin_transaction`. If a entity is
        returned, it will be transformed to it's corresponding model.
        """
        original_transaction = self.__session.begin_transaction(metadata, timeout)
        return LoomiTransaction(original_transaction, self.__client)


class LoomiAsyncSession(AsyncSession):
    """
    Wrapper for `neo4j.AsyncSession` allowing for automatic transformation of entities returned by
    queries.
    """

    __session: AsyncSession
    __client: LoomiAsyncClient

    def __init__(self, session: AsyncSession, client: LoomiAsyncClient):
        self.__session = session
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__session, name)

    async def __aenter__(self):
        await self.__session.__aenter__()
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        return await self.__session.__aexit__(
            exception_type, exception_value, traceback
        )

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
        original_result = await self.__session.run(query, parameters, **kwargs)
        return LoomiAsyncResult(original_result, self.__client)

    async def begin_transaction(
        self, metadata: Dict[str, Any] | None = None, timeout: float | None = None
    ) -> LoomiAsyncTransaction:
        """
        Method providing the same interface as `neo4j.AsyncSession.begin_transaction`. If a entity is
        returned, it will be transformed to it's corresponding model.
        """
        original_transaction = await self.__session.begin_transaction(metadata, timeout)
        return LoomiAsyncTransaction(original_transaction, self.__client)
