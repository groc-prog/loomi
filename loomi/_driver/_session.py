# pylint: disable=super-init-not-called

from typing import TYPE_CHECKING

from neo4j import Session

from loomi._driver._result import LoomiResult

if TYPE_CHECKING:
    from loomi.client.sync_client import LoomiClient
else:
    LoomiClient = object


class LoomiSession(Session):
    __session: Session
    __client: LoomiClient

    def __init__(self, session: Session, client: LoomiClient):
        self.__session = session
        self.__client = client

    def __getattr__(self, name: str):
        return getattr(self.__session, name)

    def __enter__(self):
        super().__enter__()
        return self

    def run(self, *args, **kwargs) -> LoomiResult:
        result = self.__session.run(*args, **kwargs)
        return LoomiResult(result, self.__client)
