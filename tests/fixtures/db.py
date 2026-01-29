# pylint: disable=missing-class-docstring, line-too-long, redefined-outer-name

from dataclasses import dataclass
from enum import StrEnum
from os import environ
from typing import Optional, cast

import pytest
from neo4j import AsyncGraphDatabase, GraphDatabase

from loomi.models.constraint import _MEMGRAPH_DATA_TYPE_MAPPING, MemgraphConstraintType
from loomi.models.index import MemgraphIndexType


class ServerName(StrEnum):
    NEO4J = "neo4j"
    MEMGRAPH = "memgraph"


@dataclass
class DriverSpec:
    name: str
    uri: Optional[str]
    user: Optional[str]
    pwd: Optional[str]


@pytest.fixture(
    params=[
        DriverSpec(
            name=ServerName.NEO4J,
            uri=environ.get("NEO4J_URI", None),
            user=environ.get("NEO4J_USER", None),
            pwd=environ.get("NEO4J_PWD", None),
        ),
        DriverSpec(
            name=ServerName.MEMGRAPH,
            uri=environ.get("MEMGRAPH_URI", None),
            user=environ.get("MEMGRAPH_USER", None),
            pwd=environ.get("MEMGRAPH_PWD", None),
        ),
    ],
    ids=[ServerName.NEO4J, ServerName.MEMGRAPH],
)
def driver_spec(request) -> DriverSpec:
    """The Source of Truth for driver configuration."""
    spec = cast(DriverSpec, request.param)
    if not spec.uri or not spec.user or not spec.pwd:
        pytest.skip(f"Missing environment variables for {spec.name} connection.")
    return spec


@pytest.fixture
def sync_driver(driver_spec: DriverSpec):
    """Provides a synchronous driver and cleans the database."""
    driver = GraphDatabase.driver(
        cast(str, driver_spec.uri), auth=(cast(str, driver_spec.user), cast(str, driver_spec.pwd))
    )

    # Clear all existing entities, indexes and constraints
    with driver.session() as session:
        result = session.run("MATCH (n) DETACH DELETE n")
        result.consume()

        match driver_spec.name:
            case ServerName.NEO4J:
                constraints = session.run("SHOW CONSTRAINTS")
                for constraint in constraints.values():
                    session.run(f"DROP CONSTRAINT {constraint[1]}")  # type: ignore

                indexes = session.run("SHOW INDEXES")
                for index in indexes.values():
                    session.run(f"DROP INDEX {index[1]}")  # type: ignore
            case ServerName.MEMGRAPH:
                constraints = session.run("SHOW CONSTRAINT INFO")
                for constraint in constraints.values():
                    match constraint[0]:
                        case MemgraphConstraintType.EXISTS.value:
                            session.run(f"DROP CONSTRAINT ON (n:{constraint[1]}) ASSERT EXISTS (n.{constraint[2]})")  # type: ignore
                        case MemgraphConstraintType.UNIQUE.value:
                            session.run(f"DROP CONSTRAINT ON (n:{constraint[1]}) ASSERT {', '.join([f'n.{constraint_property}' for constraint_property in constraint[2]])} IS UNIQUE")  # type: ignore
                        case MemgraphConstraintType.DATA_TYPE.value:
                            session.run(
                                f"DROP CONSTRAINT ON (n:{constraint[1]}) ASSERT n.{constraint[2]} IS TYPED {_MEMGRAPH_DATA_TYPE_MAPPING[constraint[3]]}"  # type: ignore
                            )

                indexes = session.run("SHOW INDEX INFO")
                for index in indexes.values():
                    match index[0]:
                        case MemgraphIndexType.EDGE_TYPE.value:
                            session.run(f"DROP EDGE INDEX ON :{index[1]}")  # type: ignore
                        case MemgraphIndexType.EDGE_AND_PROPERTY.value:
                            session.run(f"DROP GLOBAL EDGE INDEX ON :({index[2]})")  # type: ignore
                        case MemgraphIndexType.EDGE_TYPE_AND_PROPERTY.value:
                            session.run(f"DROP EDGE INDEX ON :{index[1]}({index[2]})")  # type: ignore
                        case MemgraphIndexType.LABEL.value:
                            session.run(f"DROP INDEX ON :{index[1]}")  # type: ignore
                        case MemgraphIndexType.LABEL_AND_PROPERTY.value:
                            session.run(
                                f"DROP INDEX ON :{index[1]}({', '.join(index[2]) if isinstance(index[2], list) else index[2]})",  # type: ignore
                            )
                        case MemgraphIndexType.POINT.value:
                            session.run(f"DROP POINT INDEX ON :{index[1]}({index[2]})")  # type: ignore
            case _:
                pytest.skip(f"Unknown spec {driver_spec.name} found")

    yield driver

    driver.close()


@pytest.fixture
async def async_driver(driver_spec: DriverSpec):
    """Provides an asynchronous driver and cleans the database."""
    driver = AsyncGraphDatabase.driver(
        cast(str, driver_spec.uri), auth=(cast(str, driver_spec.user), cast(str, driver_spec.pwd))
    )

    # Clear all existing entities, indexes and constraints
    async with driver.session() as session:
        result = await session.run("MATCH (n) DETACH DELETE n")
        await result.consume()

        match driver_spec.name:
            case ServerName.NEO4J:
                constraints = await session.run("SHOW CONSTRAINTS")
                for constraint in await constraints.values():
                    await session.run(f"DROP CONSTRAINT {constraint[1]}")  # type: ignore

                indexes = await session.run("SHOW INDEXES")
                for index in await indexes.values():
                    session.run(f"DROP INDEX {index[1]}")  # type: ignore
            case ServerName.MEMGRAPH:
                constraints = await session.run("SHOW CONSTRAINT INFO")
                for constraint in await constraints.values():
                    match constraint[0]:
                        case MemgraphConstraintType.EXISTS.value:
                            await session.run(f"DROP CONSTRAINT ON (n:{constraint[1]}) ASSERT EXISTS (n.{constraint[2]})")  # type: ignore
                        case MemgraphConstraintType.UNIQUE.value:
                            await session.run(f"DROP CONSTRAINT ON (n:{constraint[1]}) ASSERT {', '.join([f'n.{constraint_property}' for constraint_property in constraint[2]])} IS UNIQUE")  # type: ignore
                        case MemgraphConstraintType.DATA_TYPE.value:
                            await session.run(
                                f"DROP CONSTRAINT ON (n:{constraint[1]}) ASSERT n.{constraint[2]} IS TYPED {_MEMGRAPH_DATA_TYPE_MAPPING[constraint[3]]}"  # type: ignore
                            )

                indexes = await session.run("SHOW INDEX INFO")
                for index in await indexes.values():
                    match index[0]:
                        case MemgraphIndexType.EDGE_TYPE.value:
                            await session.run(f"DROP EDGE INDEX ON :{index[1]}")  # type: ignore
                        case MemgraphIndexType.EDGE_AND_PROPERTY.value:
                            await session.run(f"DROP GLOBAL EDGE INDEX ON :({index[2]})")  # type: ignore
                        case MemgraphIndexType.EDGE_TYPE_AND_PROPERTY.value:
                            await session.run(f"DROP EDGE INDEX ON :{index[1]}({index[2]})")  # type: ignore
                        case MemgraphIndexType.LABEL.value:
                            await session.run(f"DROP INDEX ON :{index[1]}")  # type: ignore
                        case MemgraphIndexType.LABEL_AND_PROPERTY.value:
                            await session.run(
                                f"DROP INDEX ON :{index[1]}({', '.join(index[2]) if isinstance(index[2], list) else index[2]})",  # type: ignore
                            )
                        case MemgraphIndexType.POINT.value:
                            await session.run(f"DROP POINT INDEX ON :{index[1]}({index[2]})")  # type: ignore
            case _:
                pytest.skip(f"Unknown spec {driver_spec.name} found")

    yield driver

    await driver.close()
