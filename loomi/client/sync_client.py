from typing import Any, Literal, Optional, Union, overload

from neo4j import Driver, Session

from loomi._driver._session import LoomiSession
from loomi.client._base import _LoomiBaseClient
from loomi.models.base import LoomiBaseConfiguration


class LoomiClient(_LoomiBaseClient):
    """Database client for interacting with Loomi models."""

    __driver: Driver

    def __init__(
        self,
        driver: Driver,
        config: Optional[LoomiBaseConfiguration] = None,
    ) -> None:
        super().__init__(config)

        self.__driver = driver

    @overload
    def session(
        self, to_models: Literal[True] = True, **session_config: Any
    ) -> LoomiSession: ...

    @overload
    def session(self, to_models: Literal[False], **session_config: Any) -> Session: ...

    def session(
        self,
        to_models: bool = True,
        **session_config: Any,
    ) -> Union[Session, LoomiSession]:
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
            return LoomiSession(session, self)

        return session
