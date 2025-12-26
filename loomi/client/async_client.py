from typing import Any, Literal, Optional, Union, overload

from neo4j import AsyncDriver, Session

from loomi._driver._session import LoomiSession
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
