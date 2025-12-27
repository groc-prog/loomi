from typing import Any, Literal, Optional, Union, overload

from neo4j import AsyncDriver, AsyncSession

from loomi._driver._session import LoomiAsyncSession
from loomi.client._base import _LoomiBaseClient
from loomi.models.base import LoomiBaseConfiguration


class LoomiAsyncClient(_LoomiBaseClient):
    """Database client for interacting with Loomi models."""

    __driver: AsyncDriver

    def __init__(
        self,
        driver: AsyncDriver,
        config: Optional[LoomiBaseConfiguration] = None,
    ) -> None:
        super().__init__(config)

        self.__driver = driver

    @overload
    def session(
        self, to_models: Literal[True] = True, **session_config: Any
    ) -> LoomiAsyncSession: ...

    @overload
    def session(
        self, to_models: Literal[False], **session_config: Any
    ) -> AsyncSession: ...

    def session(
        self,
        to_models: bool = True,
        **session_config: Any,
    ) -> Union[AsyncSession, LoomiAsyncSession]:
        """
        Start a new session. This behaves the same as the `.session()` from the driver except it
        will transform any entities contained in the result of any queries into their corresponding
        models (if possible).

        Args:
            to_models (bool): Whether to transform results into registered models (if possible).
            Defaults to `True`.
            session_config: Key-word arguments passed to the session directly.
        """
        session = self.__driver.session(**session_config)

        if to_models:
            return LoomiAsyncSession(session, self)

        return session
