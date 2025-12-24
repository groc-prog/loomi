import asyncio
from inspect import isawaitable
from typing import Awaitable, Callable, Generic, ParamSpec, TypeVar, Union

from neo4j import AsyncDriver, AsyncGraphDatabase, Driver, GraphDatabase

from loomi.client import Client

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

memgraph_driver = AsyncGraphDatabase.driver(
    "bolt://localhost:7688", auth=("memgraph", "password")
)


async def main():
    c1 = Client(neo4j_driver)
    c2 = Client(memgraph_driver)

    c1.initialize().sync()
    pass


asyncio.run(main())
