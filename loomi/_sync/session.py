# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING, Any, Dict, LiteralString, Optional, Union

import neo4j

from loomi._logger import logger
from loomi._sync.change_tracker import ChangeTracker
from loomi._sync.result import Result
from loomi._sync.transaction import Transaction

if TYPE_CHECKING:
    from loomi._sync.client import Client

    _Base = neo4j.Session
else:
    Client = object
    _Base = object


class Session(_Base):
    """Wrapper for `neo4j.Session` allowing for additional functionality."""

    __session: neo4j.Session
    __client: Client
    __change_tracker: ChangeTracker

    def __init__(self, session: neo4j.Session, client: Client):
        self.__session = session
        self.__client = client
        self.__change_tracker = ChangeTracker(session, client)

    def __getattr__(self, name: str):
        return getattr(self.__session, name)

    def __enter__(self):
        self.__session.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        return self.__session.__exit__(exception_type, exception_value, traceback)

    @property
    def change_tracker(self) -> ChangeTracker:
        """
        Change tracker exposed by this session. Will be used when `tracking` is set to `true` in a
        query.
        """
        return self.__change_tracker

    def run(
        self,
        query: Union[LiteralString, neo4j.Query],
        parameters: Optional[Dict[str, Any]] = None,
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

        logger.info("Query: %s -- Parameters: [%s]", logging_query, logging_parameters)
        original_result = self.__session.run(query, parameters, **kwargs)
        return Result(original_result, self.__client, self.__change_tracker if tracking else None)

    def begin_transaction(
        self, metadata: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> Transaction:
        """
        Method providing the same interface as `neo4j.Session.begin_transaction`. If any entity
        is returned, it will be transformed to it's corresponding model.
        """
        original_transaction = self.__session.begin_transaction(metadata, timeout)
        return Transaction(original_transaction, self.__client)
