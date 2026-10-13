# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

from typing import List, LiteralString, cast

import neo4j
import pytest
from pydantic import BaseModel

from loomi._async.client import AsyncClient
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api._core.context import CompilationContext
from loomi.query_api._core.expressions import CompoundExpression, Expression
from loomi.query_api.functions.collection import any_, none
from loomi.query_api.functions.comparison import and_, equals, or_, xor
from loomi.query_api.functions.transformation import to_lower, trim
from tests.conftest import MEMGRAPH_DRIVER_SPEC, async_cleanup


class Event(BaseModel):
    name: str
    tags: List[str]


class Person(Node):
    name: str
    age: int
    active: bool
    events: List[Event]


class Drinks(Relationship):
    name: str
    amount: int
    available: bool
    events: List[Event]


@pytest.fixture
def node_compilation_context(driver_spec):
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(driver_spec.name)
    ctx.add_model(Person)

    return ctx


@pytest.fixture
def relationship_compilation_context(driver_spec):
    """Provide an initialized compilation context for query API test models."""
    ctx = CompilationContext(driver_spec.name)
    ctx.add_model(Drinks)

    return ctx


class TestExpressionQueries:
    async def test_simple_node_expression_query(self, async_driver, node_compilation_context):
        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 20, active: true})
                """
            )

        expression = equals(Person.active, False)
        compiled = expression._compile_expression(node_compilation_context)
        query_string = compiled.to_query_string()

        async with async_driver.session() as session:
            result = await session.run(
                f"MATCH (v0) WHERE {query_string} RETURN v0",
                node_compilation_context.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "Bob"

    async def test_compound_node_expression_query(self, async_driver, node_compilation_context):
        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true})
                CREATE (:Person {name: 'Bob', age: 40, active: false})
                CREATE (:Person {name: 'Charlie', age: 20, active: true})
                """
            )

        expression = and_(equals(Person.active, True), equals(Person.name, "Alice"))
        query_string = expression.to_query_string(node_compilation_context)

        async with async_driver.session() as session:
            result = await session.run(
                f"MATCH (v0) WHERE {query_string} RETURN v0",
                node_compilation_context.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "Alice"

    async def test_memgraph_node_list_expression_optimization_query(self):
        ctx = CompilationContext(MEMGRAPH_DRIVER_SPEC.name)
        ctx.add_model(Person)
        driver = neo4j.AsyncGraphDatabase.driver(
            cast(str, MEMGRAPH_DRIVER_SPEC.uri),
            auth=(cast(str, MEMGRAPH_DRIVER_SPEC.user), cast(str, MEMGRAPH_DRIVER_SPEC.pwd)),
        )

        await async_cleanup(driver, MEMGRAPH_DRIVER_SPEC.name)
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: 'Alice', age: 30, active: true, events: [{name: 'birthday', tags: ['once-per-year']}]})
                CREATE (:Person {name: 'Bob', age: 40, active: false, events: [{name: 'workweek-start', tags: ['weekly']}]})
                """
            )

        expression = or_(
            equals(any_(Person.events).name, "birthday"),
            equals(any_(none(Person.events).tags), "weekly"),
        )
        query_string = expression.to_query_string(ctx)

        async with driver.session() as session:
            result = await session.run(
                cast(LiteralString, f"MATCH (v0) WHERE {query_string} RETURN v0"),
                ctx.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "Alice"

        await driver.close()

    async def test_node_expression_with_db_functions_query(
        self, async_driver, node_compilation_context
    ):
        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Person {name: '  Alice  ', age: 30, active: true})
                CREATE (:Person {name: ' Bob  ', age: 40, active: false})
                CREATE (:Person {name: '  Charlie ', age: 20, active: true})
                """
            )

        expression = equals(to_lower(trim(Person.name)), to_lower(trim("   Alice ")))
        compiled = expression._compile_expression(node_compilation_context)
        query_string = compiled.to_query_string()

        async with async_driver.session() as session:
            result = await session.run(
                f"MATCH (v0) WHERE {query_string} RETURN v0",
                node_compilation_context.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "  Alice  "

    async def test_simple_relationship_expression_query(
        self, async_driver, relationship_compilation_context
    ):
        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Test)-[:Drinks {name: 'Mojito', amount: 30, available: true}]->(:Test)
                CREATE (:Test)-[:Drinks {name: 'Old Fashioned', amount: 40, available: false}]->(:Test)
                CREATE (:Test)-[:Drinks {name: 'Margarita', amount: 20, available: true}]->(:Test)
                """
            )

        expression = equals(Drinks.available, False)
        compiled = expression._compile_expression(relationship_compilation_context)
        query_string = compiled.to_query_string()

        async with async_driver.session() as session:
            result = await session.run(
                f"MATCH ()-[v0]->() WHERE {query_string} RETURN v0",
                relationship_compilation_context.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "Old Fashioned"

    async def test_compound_relationship_expression_query(
        self, async_driver, relationship_compilation_context
    ):
        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Test)-[:Drinks {name: 'Mojito', amount: 30, available: true}]->(:Test)
                CREATE (:Test)-[:Drinks {name: 'Old Fashioned', amount: 40, available: false}]->(:Test)
                CREATE (:Test)-[:Drinks {name: 'Margarita', amount: 20, available: true}]->(:Test)
                """
            )

        expression = and_(equals(Drinks.available, True), equals(Drinks.name, "Mojito"))
        query_string = expression.to_query_string(relationship_compilation_context)

        async with async_driver.session() as session:
            result = await session.run(
                f"MATCH ()-[v0]->() WHERE {query_string} RETURN v0",
                relationship_compilation_context.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "Mojito"

    async def test_memgraph_relationship_list_expression_optimization_query(self):
        ctx = CompilationContext(MEMGRAPH_DRIVER_SPEC.name)
        ctx.add_model(Drinks)
        driver = neo4j.AsyncGraphDatabase.driver(
            cast(str, MEMGRAPH_DRIVER_SPEC.uri),
            auth=(cast(str, MEMGRAPH_DRIVER_SPEC.user), cast(str, MEMGRAPH_DRIVER_SPEC.pwd)),
        )

        await async_cleanup(driver, MEMGRAPH_DRIVER_SPEC.name)
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Test)-[:Drinks {name: 'Mojito', amount: 30, available: true, events: [{name: 'release', tags: ['once']}]}]->(:Test)
                CREATE (:Test)-[:Drinks {name: 'Margarita', amount: 20, available: true, events: [{name: 'restock', tags: ['weekly']}]}]->(:Test)
                """
            )

        expression = or_(
            equals(any_(Drinks.events).name, "release"),
            equals(any_(none(Drinks.events).tags), "weekly"),
        )
        query_string = expression.to_query_string(ctx)

        async with driver.session() as session:
            result = await session.run(
                cast(LiteralString, f"MATCH ()-[v0]->() WHERE {query_string} RETURN v0"),
                ctx.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == "Mojito"

        await driver.close()

    async def test_relationship_expression_with_db_functions_query(
        self, async_driver, relationship_compilation_context
    ):
        async with async_driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            await session.run(
                """
                CREATE (:Test)-[:Drinks {name: ' Mojito   ', amount: 30, available: true}]->(:Test)
                CREATE (:Test)-[:Drinks {name: '  Old Fashioned ', amount: 40, available: false}]->(:Test)
                CREATE (:Test)-[:Drinks {name: '  Margarita  ', amount: 20, available: true}]->(:Test)
                """
            )

        expression = equals(to_lower(trim(Drinks.name)), to_lower(trim("    Mojito    ")))
        compiled = expression._compile_expression(relationship_compilation_context)
        query_string = compiled.to_query_string()

        async with async_driver.session() as session:
            result = await session.run(
                f"MATCH ()-[v0]->() WHERE {query_string} RETURN v0",
                relationship_compilation_context.get_parameters(),
            )
            records = await result.values()

            assert len(records) == 1
            assert len(records[0]) == 1
            assert dict(records[0][0])["name"] == " Mojito   "
