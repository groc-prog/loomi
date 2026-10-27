# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest

from loomi._async.client import AsyncClient
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api._builders.update_builder import UpdateResult
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
from loomi.query_api.functions.transformation import to_upper


class Adult(Node):
    name: str
    age: int

    loomi_config = {"labels": {"Adult"}}


class Child(Node):
    name: str

    loomi_config = {"labels": {"Child"}}


class HasChild(Relationship):
    nth_child: int
    kind: str

    loomi_config = {"type": "HAS_CHILD"}


@pytest.fixture
async def seed_data(async_driver):
    async with async_driver.session() as session:
        for i in range(5):
            await session.run(
                "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c)",
                {
                    "a": {"name": f"Adult:{i}", "age": i},
                    "b": {"nth_child": i, "kind": "boy"},
                    "c": {"name": f"Child:{i}"},
                },
            )


class TestAsyncClientUpdate:
    async def test_async_client_update_passes_kwargs_to_session(
        self, async_driver, seed_data, mocker
    ):
        session_spy = mocker.spy(neo4j.AsyncSession, "run")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        test_fetch_size = 1000

        session_spy.reset_mock()
        await client.update(Adult, fetch_size=test_fetch_size).set("name", "update").execute()
        session_spy.assert_called_once_with(
            mocker.ANY, mocker.ANY, mocker.ANY, fetch_size=test_fetch_size
        )

    async def test_async_client_update_accepts_transaction(self, async_driver, seed_data, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            async with await session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                await client.update(Adult, tx).set("name", "update").execute()
                tx_run_spy.assert_called_once()
                session_run_spy.assert_not_called()

    async def test_async_client_update_passes_kwargs_to_transaction(
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

                await client.update(Adult, tx, timeout=test_timeout).set("name", "update").execute()
                tx_run_spy.assert_called_once_with(mocker.ANY, mocker.ANY, timeout=test_timeout)
                session_run_spy.assert_not_called()


class TestAsyncClientUpdateNodes:
    async def test_async_client_update_nodes_updates_all_nodes(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN id(a), elementId(a)")
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(Adult).set(Adult.name, "updated").execute()
        assert isinstance(result, UpdateResult)
        assert result.affected == 5

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"


class TestAsyncClientUpdateNodesWhere:
    async def test_async_client_update_nodes_where_only_updates_filtered_entities(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN id(a), elementId(a)",
                {"name": "Adult:0"},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(Adult)
            .where(ends_with(Adult.name, "0"))
            .set(Adult.name, "updated")
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN a", {"name": "updated"}
            )
            values = await result.values()
            assert len(values) == 1

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    async def test_async_client_update_nodes_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN id(a), elementId(a)",
                {"name": "Adult:0"},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(Adult)
            .where(starts_with(Adult.name, "Adult"))
            .where(ends_with(Adult.name, "0"))
            .set(Adult.name, "updated")
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN a", {"name": "updated"}
            )
            values = await result.values()
            assert len(values) == 1

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    async def test_async_client_update_nodes_where_with_compound_filters(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name = $name1 OR a.name = $name2 RETURN id(a), elementId(a)",
                {"name1": "Adult:0", "name2": "Adult:4"},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(Adult)
            .where(or_(ends_with(Adult.name, "0"), ends_with(Adult.name, "4")))
            .set(Adult.name, "updated")
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) WHERE a.name = $name RETURN a", {"name": "updated"}
            )
            values = await result.values()
            assert len(values) == 2

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    async def test_async_client_update_nodes_where_raises_if_invalid_expression_provided(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            await client.update(Adult).where(2 == 2).set(Adult.name, "updated").execute()


class TestAsyncClientUpdateNodesSet:
    async def test_async_client_update_nodes_set_with_descriptor(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(Adult).set(Adult.name, "updated").execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    async def test_async_client_update_nodes_set_with_field_name(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(Adult).set("name", "updated").execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "updated"

    async def test_async_client_update_nodes_set_with_expression_value(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(Adult).set(Adult.age, Adult.age + 20).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["age"] >= 20

    async def test_async_client_update_nodes_set_with_db_function(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(Adult).set(Adult.name, to_upper(Adult.name)).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"].startswith("ADULT:")

    async def test_async_client_update_nodes_set_overwrites_field_update_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH (a:Adult) RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(Adult).set(Adult.name, "updated").set(Adult.name, "other").execute()
        )
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH (a:Adult) RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["name"] == "other"

    async def test_async_client_update_nodes_set_raises_if_field_descriptor_is_for_wrong_model(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid field found. Expected a valid field of model {Adult.__name__}, got name",
        ):
            await client.update(Adult).set(Child.name, "updated").execute()


class TestAsyncClientUpdateRelationships:
    async def test_async_client_update_relationships_updates_all_relationships(
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

        result = await client.update(HasChild).set(HasChild.nth_child, 10).execute()
        assert isinstance(result, UpdateResult)
        assert result.affected == 5

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10


class TestAsyncClientUpdateRelationshipsWhere:
    async def test_async_client_update_relationships_where_only_updates_filtered_entities(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN id(a), elementId(a)",
                {"count": 0},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(HasChild)
            .where(equals(HasChild.nth_child, 0))
            .set(HasChild.nth_child, 10)
            .execute()
        )
        assert result.affected == 1
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = await result.values()
            assert len(values) == 1

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    async def test_async_client_update_relationships_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count1 OR a.nth_child = $count2 RETURN id(a), elementId(a)",
                {"count1": 0, "count2": 1},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(HasChild)
            .where(greater_than_or_equal(HasChild.nth_child, 0))
            .where(less_than_or_equal(HasChild.nth_child, 1))
            .set(HasChild.nth_child, 10)
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = await result.values()
            assert len(values) == 2

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    async def test_async_client_update_relationships_where_with_compound_filters(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count1 OR a.nth_child = $count2 RETURN id(a), elementId(a)",
                {"count1": 2, "count2": 3},
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(HasChild)
            .where(or_(equals(HasChild.nth_child, 2), equals(HasChild.nth_child, 3)))
            .set(HasChild.nth_child, 10)
            .execute()
        )
        assert result.affected == 2
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() WHERE a.nth_child = $count RETURN a", {"count": 10}
            )
            values = await result.values()
            assert len(values) == 2

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    async def test_async_client_update_relationships_where_raises_if_invalid_expression_provided(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            await client.update(HasChild).where(2 == 2).set(HasChild.nth_child, 10).execute()


class TestAsyncClientUpdateRelationshipsSet:
    async def test_async_client_update_relationships_set_with_descriptor(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(HasChild).set(HasChild.nth_child, 10).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    async def test_async_client_update_relationships_set_with_field_name(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(HasChild).set("nth_child", 10).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 10

    async def test_async_client_update_relationships_set_with_expression_value(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(HasChild).set(HasChild.nth_child, HasChild.nth_child + 20).execute()
        )
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] >= 20

    async def test_async_client_update_relationships_set_with_db_function(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = await client.update(HasChild).set(HasChild.kind, to_upper(HasChild.kind)).execute()
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["kind"].startswith("BOY")

    async def test_async_client_update_relationships_set_overwrites_field_update_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with async_driver.session() as session:
            result = await session.run(
                "MATCH ()-[a:HAS_CHILD]->() RETURN id(a), elementId(a)",
            )
            values = await result.values()

            ids = [value[0] for value in values]
            element_ids = [value[1] for value in values]

        result = (
            await client.update(HasChild)
            .set(HasChild.nth_child, 10)
            .set(HasChild.nth_child, 40)
            .execute()
        )
        assert result.affected == 5
        assert isinstance(result, UpdateResult)

        for element_id, id_ in result.affected_ids:
            assert element_id in element_ids
            assert id_ in ids

        async with async_driver.session() as session:
            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a")
            values = await result.values()
            assert len(values) == 5

            for value in values[0]:
                assert value.element_id in element_ids
                assert value["nth_child"] == 40

    async def test_async_client_update_relationships_set_raises_if_field_descriptor_is_for_wrong_model(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid field found. Expected a valid field of model {HasChild.__name__}, got name",
        ):
            await client.update(HasChild).set(Adult.name, "name").execute()
