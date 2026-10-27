# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest
from pydantic import BaseModel

from loomi._async.client import AsyncClient
from loomi.exceptions import QueryError
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from loomi.query_api._core.expressions import CompoundExpression
from loomi.query_api._core.protocols import CompilableExpression
from loomi.query_api.constants import OrderBy
from loomi.query_api.functions.comparison import (
    ends_with,
    equals,
    greater_than,
    less_than,
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


class TestAsyncClientQuery:
    async def test_async_client_query_passes_kwargs_to_session(
        self, async_driver, seed_data, mocker
    ):
        session_spy = mocker.spy(neo4j.AsyncSession, "run")

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        test_fetch_size = 1000

        session_spy.reset_mock()
        await client.query(Adult, fetch_size=test_fetch_size).execute()
        session_spy.assert_called_once_with(
            mocker.ANY, mocker.ANY, mocker.ANY, fetch_size=test_fetch_size
        )

    async def test_async_client_query_accepts_transaction(self, async_driver, seed_data, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        async with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            async with await session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                await client.query(Adult, tx).execute()
                tx_run_spy.assert_called_once()
                session_run_spy.assert_not_called()

    async def test_async_client_query_passes_kwargs_to_transaction(
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

                await client.query(Adult, tx, timeout=test_timeout).execute()
                tx_run_spy.assert_called_once_with(mocker.ANY, mocker.ANY, timeout=test_timeout)
                session_run_spy.assert_not_called()


class TestAsyncClientQueryNodes:
    async def test_async_client_query_nodes_returns_all_nodes(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for model in models:
            [prefix, suffix] = model.name.split(":")
            assert prefix == "Adult"

            int_suffix = int(suffix)
            assert 0 <= int_suffix <= 4

    async def test_async_client_query_nodes_returns_empty_list_if_no_matches_found(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestAsyncClientQueryNodesWhere:
    async def test_async_client_query_nodes_where_filters_results(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).where(ends_with(Adult.name, "0")).execute()
        assert isinstance(models, list)
        assert len(models) == 1

        model = models[0]
        assert isinstance(model, Adult)
        assert model.name == "Adult:0"

    async def test_async_client_query_nodes_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(Adult)
            .where(starts_with(Adult.name, "Adult"))
            .where(ends_with(Adult.name, "0"))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 1

        model = models[0]
        assert isinstance(model, Adult)
        assert model.name == "Adult:0"

    async def test_async_client_query_nodes_where_with_compound_filters(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(Adult)
            .where(or_(ends_with(Adult.name, "0"), ends_with(Adult.name, "4")))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, Adult) for model in models)

        for model in models:
            [prefix, suffix] = model.name.split(":")
            assert prefix == "Adult"
            assert suffix in ["0", "4"]

    async def test_async_client_query_nodes_where_raises_if_invalid_expression_provided(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            await client.query(Adult).where(2 == 2).execute()


class TestAsyncClientQueryNodesOrderBy:
    async def test_async_client_query_nodes_order_by_field_name_uses_database_default_if_not_defined(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by("name").execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_field_name_asc(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by("name", OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_field_name_desc(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by("name", OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_descriptor_asc(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by(Adult.name, OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_descriptor_desc(self, async_driver, seed_data):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by(Adult.name, OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_dict_with_descriptor_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by({Adult.name: OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_dict_with_str_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).order_by({"name": OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_overwrites_field_order_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(Adult)
            .order_by(Adult.name, OrderBy.DESC)
            .order_by(Adult.name, OrderBy.ASC)
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    async def test_async_client_query_nodes_order_by_raises_if_field_not_defined_on_model(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(QueryError, match="foobar is not a valid field to order by"):
            await client.query(Adult).order_by("foobar").execute()


class TestAsyncClientQueryNodesLimit:
    async def test_async_client_query_nodes_limit_returns_limited_number_of_results(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).limit(2).execute()
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, Adult) for model in models)

    async def test_async_client_query_nodes_limit_overwrites_limit_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).limit(2).limit(4).execute()
        assert isinstance(models, list)
        assert len(models) == 4
        assert all(isinstance(model, Adult) for model in models)

    async def test_async_client_query_nodes_limit_raises_if_limit_is_invalid(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(QueryError, match="limit must be a positive integer if defined"):
            await client.query(Adult).limit(-2).execute()

    async def test_async_client_query_nodes_limit_can_be_called_with_limit_zero(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).limit(0).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestAsyncClientQueryNodesSkip:
    async def test_async_client_query_nodes_skip_returns_results_with_first_x_results_skipped(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).skip(2).execute()
        assert isinstance(models, list)
        assert len(models) == 3
        assert all(isinstance(model, Adult) for model in models)

    async def test_async_client_query_nodes_skip_overwrites_skip_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).skip(2).skip(4).execute()
        assert isinstance(models, list)
        assert len(models) == 1
        assert all(isinstance(model, Adult) for model in models)

    async def test_async_client_query_nodes_skip_raises_if_skip_is_invalid(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(QueryError, match="skip must be a positive integer if defined"):
            await client.query(Adult).skip(-2).execute()

    async def test_async_client_query_nodes_skip_can_be_called_with_skip_zero(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).skip(0).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)


class TestAsyncClientQueryNodesProject:
    async def test_async_client_query_nodes_project_as_dict_with_descriptor_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).project({Adult.name: "my_name"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_name" in model for model in models)
        assert all(model["my_name"].startswith("Adult:") for model in models)

    async def test_async_client_query_nodes_project_as_dict_with_str_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).project({"name": "my_name"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_name" in model for model in models)
        assert all(model["my_name"].startswith("Adult:") for model in models)

    async def test_async_client_query_nodes_project_as_model(self, async_driver, seed_data):
        class Projection(BaseModel):
            name: str

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).project(Projection).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Projection) for model in models)
        assert all(model.name.startswith("Adult:") for model in models)

    async def test_async_client_query_nodes_project_returns_unknown_keys_as_none(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(Adult).project({"foobar": "my_foo"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_foo" in model for model in models)
        assert all(model["my_foo"] is None for model in models)

    async def test_async_client_query_nodes_project_overwrites_projection_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(Adult)
            .project({Adult.name: "my_name"})
            .project({Adult.name: "other_name"})
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("other_name" in model for model in models)
        assert all(model["other_name"].startswith("Adult:") for model in models)


class TestAsyncClientQueryRelationships:
    async def test_async_client_query_relationships_returns_all_nodes(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for model in models:
            assert 0 <= model.nth_child <= 4

    async def test_async_client_query_relationships_returns_empty_list_if_no_matches_found(
        self, async_driver
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestAsyncClientQueryRelationshipsWhere:
    async def test_async_client_query_relationships_where_filters_results(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).where(equals(HasChild.nth_child, 0)).execute()
        assert isinstance(models, list)
        assert len(models) == 1

        model = models[0]
        assert isinstance(model, HasChild)
        assert model.nth_child == 0

    async def test_async_client_query_relationships_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(HasChild)
            .where(greater_than(HasChild.nth_child, 0))
            .where(less_than(HasChild.nth_child, 4))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 3

        for model in models:
            assert 0 < model.nth_child < 4

    async def test_async_client_query_relationships_where_with_compound_filters(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(HasChild)
            .where(or_(equals(HasChild.nth_child, 2), equals(HasChild.nth_child, 4)))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, HasChild) for model in models)

        for model in models:
            assert model.nth_child in [2, 4]

    async def test_async_client_query_relationships_where_raises_if_invalid_expression_provided(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            await client.query(HasChild).where(2 == 2).execute()


class TestAsyncClientQueryRelationshipsOrderBy:
    async def test_async_client_query_relationships_order_by_field_name_uses_database_default_if_not_defined(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by("nth_child").execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_field_name_asc(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by("nth_child", OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_field_name_desc(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by("nth_child", OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_descriptor_asc(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by(HasChild.nth_child, OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_descriptor_desc(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by(HasChild.nth_child, OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_dict_with_descriptor_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by({HasChild.nth_child: OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_dict_with_str_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).order_by({"nth_child": OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_overwrites_field_order_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(HasChild)
            .order_by(HasChild.nth_child, OrderBy.DESC)
            .order_by(HasChild.nth_child, OrderBy.ASC)
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    async def test_async_client_query_relationships_order_by_raises_if_field_not_defined_on_model(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(QueryError, match="foobar is not a valid field to order by"):
            await client.query(HasChild).order_by("foobar").execute()


class TestAsyncClientQueryRelationshipsLimit:
    async def test_async_client_query_relationships_limit_returns_limited_number_of_results(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).limit(2).execute()
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, HasChild) for model in models)

    async def test_async_client_query_relationships_limit_overwrites_limit_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).limit(2).limit(4).execute()
        assert isinstance(models, list)
        assert len(models) == 4
        assert all(isinstance(model, HasChild) for model in models)

    async def test_async_client_query_relationships_limit_raises_if_limit_is_invalid(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(QueryError, match="limit must be a positive integer if defined"):
            await client.query(HasChild).limit(-2).execute()

    async def test_async_client_query_relationships_limit_can_be_called_with_limit_zero(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).limit(0).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestAsyncClientQueryRelationshipsSkip:
    async def test_async_client_query_relationships_skip_returns_results_with_first_x_results_skipped(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).skip(2).execute()
        assert isinstance(models, list)
        assert len(models) == 3
        assert all(isinstance(model, HasChild) for model in models)

    async def test_async_client_query_relationships_skip_overwrites_skip_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).skip(2).skip(4).execute()
        assert isinstance(models, list)
        assert len(models) == 1
        assert all(isinstance(model, HasChild) for model in models)

    async def test_async_client_query_relationships_skip_raises_if_skip_is_invalid(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        with pytest.raises(QueryError, match="skip must be a positive integer if defined"):
            await client.query(HasChild).skip(-2).execute()

    async def test_async_client_query_relationships_skip_can_be_called_with_skip_zero(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).skip(0).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)


class TestAsyncClientQueryRelationshipsProject:
    async def test_async_client_query_relationships_project_as_dict_with_descriptor_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).project({HasChild.nth_child: "child_num"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("child_num" in model for model in models)

        for model in models:
            assert 0 <= model["child_num"] <= 4

    async def test_async_client_query_relationships_project_as_dict_with_str_key(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).project({"nth_child": "child_num"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("child_num" in model for model in models)

        for model in models:
            assert 0 <= model["child_num"] <= 4

    async def test_async_client_query_relationships_project_as_model(self, async_driver, seed_data):
        class Projection(BaseModel):
            nth_child: int

        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).project(Projection).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Projection) for model in models)

        for model in models:
            assert 0 <= model.nth_child <= 4

    async def test_async_client_query_relationships_project_returns_unknown_keys_as_none(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = await client.query(HasChild).project({"foobar": "my_foo"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_foo" in model for model in models)
        assert all(model["my_foo"] is None for model in models)

    async def test_async_client_query_relationships_project_overwrites_projection_if_called_multiple_times(
        self, async_driver, seed_data
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        models = (
            await client.query(HasChild)
            .project({HasChild.nth_child: "child_num"})
            .project({HasChild.nth_child: "child_count"})
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("child_count" in model for model in models)

        for model in models:
            assert 0 <= model["child_count"] <= 4
