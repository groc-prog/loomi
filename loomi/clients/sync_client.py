from typing import Any, Literal, Union, overload

from neo4j import Driver, Session

from loomi._driver._session import LoomiSession
from loomi._logger import _LogContextKey, _scoped_log_ctx
from loomi.clients._base import _LoomiBaseClient


class LoomiClient(_LoomiBaseClient[Driver]):
    """Database client for interacting with Loomi models."""

    @overload
    def session(self, to_models: Literal[True] = True, **session_config: Any) -> LoomiSession: ...

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
        with _scoped_log_ctx(
            {
                _LogContextKey.DRIVER: self._driver.__class__.__name__,
                _LogContextKey.SERVER_TYPE: self._server_type,
            }
        ):
            session = self._driver.session(**session_config)

            if to_models:
                return LoomiSession(session, self)

            return session
