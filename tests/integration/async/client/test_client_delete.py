# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api._builders.delete_builder import DeleteResult
from loomi.query_api._core.expressions import CompoundExpression
from loomi.query_api._core.protocols import CompilableExpression
from loomi.query_api.functions.comparison import (
    ends_with,
    equals,
    greater_than_or_equal,
    less_than_or_equal,
    or_,
    starts_with,
)


class Adult(Node):
    name: str

    loomi_config = {"labels": {"Adult"}}


class Child(Node):
    name: str

    loomi_config = {"labels": {"Child"}}


class HasChild(Relationship):
    nth_child: int

    loomi_config = {"type": "HAS_CHILD"}


@pytest.fixture
async def seed_data(async_driver):
    async with async_driver.session() as session:
        for i in range(5):
            await session.run(
                "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c)",
                {
                    "a": {"name": f"Adult:{i}"},
                    "b": {"nth_child": i},
                    "c": {"name": f"Child:{i}"},
                },
            )


class TestAsyncClientDelete:
    async def test_async_client_delete_passes_kwargs_to_session(
        self, async_driver, seed_data, mocker
    ):
        session_spy = mocker.spy(neo4j.AsyncSession, "run")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        test_fetch_size = 1000

        session_spy.reset_mock()
        await client.delete(Adult, fetch_size=test_fetch_size).execute()
        session_spy.assert_called_once_with(
            mocker.ANY, mocker.ANY, mocker.ANY, fetch_size=test_fetch_size
        )

    async def test_async_client_delete_accepts_transaction(self, async_driver, seed_data, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            async with await session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                await client.delete(Adult, tx).execute()
                tx_run_spy.assert_called_once()
                session_run_spy.assert_not_called()

    async def test_async_client_delete_passes_kwargs_to_transaction(
        self, async_driver, seed_data, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        test_timeout = 10

        async with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            async with await session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                await client.delete(Adult, tx, timeout=test_timeout).execute()
                tx_run_spy.assert_called_once_with(mocker.ANY, mocker.ANY, timeout=test_timeout)
                session_run_spy.assert_not_called()


class TestAsyncClientDeleteNodes:
    async def test_async_client_delete_nodes_deletes_all_nodes(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN id(a), elementId(a)")
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.delete(Adult).execute()
        assert isinstance(result, DeleteResult)
        assert result.affected == 5

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 0


class TestAsyncClientDeleteNodesWhere:
    async def test_async_client_delete_nodes_where_only_deletes_filtered_entities(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name <> $name RETURN id(a), elementId(a)",
                {"name": "Adult:0"},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.delete(Adult).where(ends_with(Adult.name, "0")).execute()
        assert result.affected == 1
        assert isinstance(result, DeleteResult)

        for element_id, id_ in result.affected_ids:
            assert element_id not in element_ids
            assert id_ not in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 4

            remaining = [value[0] for value in values]
            assert all(element_id in element_ids for element_id in remaining)

    async def test_async_client_delete_nodes_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name <> $name RETURN id(a), elementId(a)",
                {"name": "Adult:0"},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.delete(Adult)
            .where(starts_with(Adult.name, "Adult"))
            .where(ends_with(Adult.name, "0"))
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, DeleteResult)

        for element_id, id_ in result.affected_ids:
            assert element_id not in element_ids
            assert id_ not in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 4

            remaining = [value[0] for value in values]
            assert all(element_id in element_ids for element_id in remaining)

    async def test_async_client_delete_nodes_where_with_compound_filters(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name <> $name1 AND a.name <> $name2 RETURN id(a), elementId(a)",
                {"name1": "Adult:0", "name2": "Adult:4"},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.delete(Adult)
            .where(or_(ends_with(Adult.name, "0"), ends_with(Adult.name, "4")))
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, DeleteResult)

        for element_id, id_ in result.affected_ids:
            assert element_id not in element_ids
            assert id_ not in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 3

            remaining = [value[0] for value in values]
            assert all(element_id in element_ids for element_id in remaining)

    async def test_async_client_delete_nodes_where_raises_if_invalid_expression_provided(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            await client.delete(Adult).where(2 == 2).execute()


class TestAsyncClientDeleteRelationships:
    async def test_async_client_delete_relationships_deletes_all_relationships(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)")
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.delete(HasChild).execute()
        assert isinstance(result, DeleteResult)
        assert result.affected == 5

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 0


class TestAsyncClientDeleteRelationshipsWhere:
    async def test_async_client_delete_relationships_where_only_deletes_filtered_entities(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child <> $count RETURN id(a), elementId(a)",
                {"count": 0},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.delete(HasChild).where(equals(HasChild.nth_child, 0)).execute()
        assert result.affected == 1
        assert isinstance(result, DeleteResult)

        for element_id, id_ in result.affected_ids:
            assert element_id not in element_ids
            assert id_ not in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 4

            remaining = [value[0] for value in values]
            assert all(element_id in element_ids for element_id in remaining)

    async def test_async_client_delete_relationships_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child <> $count1 AND a.nth_child <> $count2 RETURN id(a), elementId(a)",
                {"count1": 0, "count2": 1},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.delete(HasChild)
            .where(greater_than_or_equal(HasChild.nth_child, 0))
            .where(less_than_or_equal(HasChild.nth_child, 1))
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, DeleteResult)

        for element_id, id_ in result.affected_ids:
            assert element_id not in element_ids
            assert id_ not in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 3

            remaining = [value[0] for value in values]
            assert all(element_id in element_ids for element_id in remaining)

    async def test_async_client_delete_relationships_where_with_compound_filters(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child <> $count1 AND a.nth_child <> $count2 RETURN id(a), elementId(a)",
                {"count1": 2, "count2": 3},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.delete(HasChild)
            .where(or_(equals(HasChild.nth_child, 2), equals(HasChild.nth_child, 3)))
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, DeleteResult)

        for element_id, id_ in result.affected_ids:
            assert element_id not in element_ids
            assert id_ not in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN elementId(a)")
            values = await result.values()
            assert len(values) == 3

            remaining = [value[0] for value in values]
            assert all(element_id in element_ids for element_id in remaining)

    async def test_async_client_delete_relationships_where_raises_if_invalid_expression_provided(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            await client.delete(HasChild).where(2 == 2).execute()
