# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable


import neo4j
import pytest
from pydantic import BaseModel

from loomi._sync.client import Client
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
def seed_data(sync_driver):
    with sync_driver.session() as session:
        for i in range(5):
            session.run(
                "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c)",
                {
                    "a": {"name": f"Adult:{i}"},
                    "b": {"nth_child": i},
                    "c": {"name": f"Child:{i}"},
                },
            )


class TestSyncClientQuery:
    def test_sync_client_query_passes_kwargs_to_session(self, sync_driver, seed_data, mocker):
        session_spy = mocker.spy(neo4j.Session, "run")

        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        test_fetch_size = 1000

        session_spy.reset_mock()
        client.query(Adult, fetch_size=test_fetch_size).execute()
        session_spy.assert_called_once_with(
            mocker.ANY, mocker.ANY, mocker.ANY, fetch_size=test_fetch_size
        )

    def test_sync_client_query_accepts_transaction(self, sync_driver, seed_data, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            with session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                client.query(Adult, tx).execute()
                tx_run_spy.assert_called_once()
                session_run_spy.assert_not_called()

    def test_sync_client_query_passes_kwargs_to_transaction(self, sync_driver, seed_data, mocker):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        test_timeout = 10

        with client.session() as session:
            session_run_spy = mocker.spy(session, "run")

            with session.begin_transaction() as tx:
                tx_run_spy = mocker.spy(tx, "run")

                client.query(Adult, tx, timeout=test_timeout).execute()
                tx_run_spy.assert_called_once_with(mocker.ANY, mocker.ANY, timeout=test_timeout)
                session_run_spy.assert_not_called()


class TestSyncClientQueryNodes:
    def test_sync_client_query_nodes_returns_all_nodes(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for model in models:
            [prefix, suffix] = model.name.split(":")
            assert prefix == "Adult"

            int_suffix = int(suffix)
            assert 0 <= int_suffix <= 4

    def test_sync_client_query_nodes_returns_empty_list_if_no_matches_found(self, sync_driver):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestSyncClientQueryNodesWhere:
    def test_sync_client_query_nodes_where_filters_results(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).where(ends_with(Adult.name, "0")).execute()
        assert isinstance(models, list)
        assert len(models) == 1

        model = models[0]
        assert isinstance(model, Adult)
        assert model.name == "Adult:0"

    def test_sync_client_query_nodes_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(Adult)
            .where(starts_with(Adult.name, "Adult"))
            .where(ends_with(Adult.name, "0"))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 1

        model = models[0]
        assert isinstance(model, Adult)
        assert model.name == "Adult:0"

    def test_sync_client_query_nodes_where_with_compound_filters(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(Adult)
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

    def test_sync_client_query_nodes_where_raises_if_invalid_expression_provided(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            client.query(Adult).where(2 == 2).execute()


class TestSyncClientQueryNodesOrderBy:
    def test_sync_client_query_nodes_order_by_field_name_uses_database_default_if_not_defined(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by("name").execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_field_name_asc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by("name", OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_field_name_desc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by("name", OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_descriptor_asc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by(Adult.name, OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_descriptor_desc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by(Adult.name, OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_dict_with_descriptor_key(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by({Adult.name: OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_dict_with_str_key(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).order_by({"name": OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_overwrites_field_order_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(Adult)
            .order_by(Adult.name, OrderBy.DESC)
            .order_by(Adult.name, OrderBy.ASC)
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)

        for index, model in enumerate(models):
            assert model.name == f"Adult:{index}"

    def test_sync_client_query_nodes_order_by_raises_if_field_not_defined_on_model(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="foobar is not a valid field to order by"):
            client.query(Adult).order_by("foobar").execute()


class TestSyncClientQueryNodesLimit:
    def test_sync_client_query_nodes_limit_returns_limited_number_of_results(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).limit(2).execute()
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, Adult) for model in models)

    def test_sync_client_query_nodes_limit_overwrites_limit_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).limit(2).limit(4).execute()
        assert isinstance(models, list)
        assert len(models) == 4
        assert all(isinstance(model, Adult) for model in models)

    def test_sync_client_query_nodes_limit_raises_if_limit_is_invalid(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="limit must be a positive integer if defined"):
            client.query(Adult).limit(-2).execute()

    def test_sync_client_query_nodes_limit_can_be_called_with_limit_zero(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).limit(0).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestSyncClientQueryNodesSkip:
    def test_sync_client_query_nodes_skip_returns_results_with_first_x_results_skipped(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).skip(2).execute()
        assert isinstance(models, list)
        assert len(models) == 3
        assert all(isinstance(model, Adult) for model in models)

    def test_sync_client_query_nodes_skip_overwrites_skip_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).skip(2).skip(4).execute()
        assert isinstance(models, list)
        assert len(models) == 1
        assert all(isinstance(model, Adult) for model in models)

    def test_sync_client_query_nodes_skip_raises_if_skip_is_invalid(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="skip must be a positive integer if defined"):
            client.query(Adult).skip(-2).execute()

    def test_sync_client_query_nodes_skip_can_be_called_with_skip_zero(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).skip(0).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Adult) for model in models)


class TestSyncClientQueryNodesProject:
    def test_sync_client_query_nodes_project_as_dict_with_descriptor_key(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).project({Adult.name: "my_name"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_name" in model for model in models)
        assert all(model["my_name"].startswith("Adult:") for model in models)

    def test_sync_client_query_nodes_project_as_dict_with_str_key(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).project({"name": "my_name"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_name" in model for model in models)
        assert all(model["my_name"].startswith("Adult:") for model in models)

    def test_sync_client_query_nodes_project_as_model(self, sync_driver, seed_data):
        class Projection(BaseModel):
            name: str

        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).project(Projection).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Projection) for model in models)
        assert all(model.name.startswith("Adult:") for model in models)

    def test_sync_client_query_nodes_project_returns_unknown_keys_as_none(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(Adult).project({"foobar": "my_foo"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_foo" in model for model in models)
        assert all(model["my_foo"] is None for model in models)

    def test_sync_client_query_nodes_project_overwrites_projection_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(Adult)
            .project({Adult.name: "my_name"})
            .project({Adult.name: "other_name"})
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("other_name" in model for model in models)
        assert all(model["other_name"].startswith("Adult:") for model in models)


class TestSyncClientQueryRelationships:
    def test_sync_client_query_relationships_returns_all_nodes(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for model in models:
            assert 0 <= model.nth_child <= 4

    def test_sync_client_query_relationships_returns_empty_list_if_no_matches_found(
        self, sync_driver
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestSyncClientQueryRelationshipsWhere:
    def test_sync_client_query_relationships_where_filters_results(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).where(equals(HasChild.nth_child, 0)).execute()
        assert isinstance(models, list)
        assert len(models) == 1

        model = models[0]
        assert isinstance(model, HasChild)
        assert model.nth_child == 0

    def test_sync_client_query_relationships_where_filters_combine_with_logical_and_when_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(HasChild)
            .where(greater_than(HasChild.nth_child, 0))
            .where(less_than(HasChild.nth_child, 4))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 3

        for model in models:
            assert 0 < model.nth_child < 4

    def test_sync_client_query_relationships_where_with_compound_filters(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(HasChild)
            .where(or_(equals(HasChild.nth_child, 2), equals(HasChild.nth_child, 4)))
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, HasChild) for model in models)

        for model in models:
            assert model.nth_child in [2, 4]

    def test_sync_client_query_relationships_where_raises_if_invalid_expression_provided(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(
            QueryError,
            match=f"Invalid expression found. Expected {CompilableExpression.__name__} or {CompoundExpression.__name__}, got {True}",
        ):
            client.query(HasChild).where(2 == 2).execute()


class TestSyncClientQueryRelationshipsOrderBy:
    def test_sync_client_query_relationships_order_by_field_name_uses_database_default_if_not_defined(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by("nth_child").execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_field_name_asc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by("nth_child", OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_field_name_desc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by("nth_child", OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_descriptor_asc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by(HasChild.nth_child, OrderBy.ASC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_descriptor_desc(self, sync_driver, seed_data):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by(HasChild.nth_child, OrderBy.DESC).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(reversed(models)):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_dict_with_descriptor_key(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by({HasChild.nth_child: OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_dict_with_str_key(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).order_by({"nth_child": OrderBy.ASC}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_overwrites_field_order_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(HasChild)
            .order_by(HasChild.nth_child, OrderBy.DESC)
            .order_by(HasChild.nth_child, OrderBy.ASC)
            .execute()
        )
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)

        for index, model in enumerate(models):
            assert model.nth_child == index

    def test_sync_client_query_relationships_order_by_raises_if_field_not_defined_on_model(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="foobar is not a valid field to order by"):
            client.query(HasChild).order_by("foobar").execute()


class TestSyncClientQueryRelationshipsLimit:
    def test_sync_client_query_relationships_limit_returns_limited_number_of_results(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).limit(2).execute()
        assert isinstance(models, list)
        assert len(models) == 2
        assert all(isinstance(model, HasChild) for model in models)

    def test_sync_client_query_relationships_limit_overwrites_limit_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).limit(2).limit(4).execute()
        assert isinstance(models, list)
        assert len(models) == 4
        assert all(isinstance(model, HasChild) for model in models)

    def test_sync_client_query_relationships_limit_raises_if_limit_is_invalid(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="limit must be a positive integer if defined"):
            client.query(HasChild).limit(-2).execute()

    def test_sync_client_query_relationships_limit_can_be_called_with_limit_zero(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).limit(0).execute()
        assert isinstance(models, list)
        assert len(models) == 0


class TestSyncClientQueryRelationshipsSkip:
    def test_sync_client_query_relationships_skip_returns_results_with_first_x_results_skipped(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).skip(2).execute()
        assert isinstance(models, list)
        assert len(models) == 3
        assert all(isinstance(model, HasChild) for model in models)

    def test_sync_client_query_relationships_skip_overwrites_skip_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).skip(2).skip(4).execute()
        assert isinstance(models, list)
        assert len(models) == 1
        assert all(isinstance(model, HasChild) for model in models)

    def test_sync_client_query_relationships_skip_raises_if_skip_is_invalid(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        with pytest.raises(QueryError, match="skip must be a positive integer if defined"):
            client.query(HasChild).skip(-2).execute()

    def test_sync_client_query_relationships_skip_can_be_called_with_skip_zero(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).skip(0).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, HasChild) for model in models)


class TestSyncClientQueryRelationshipsProject:
    def test_sync_client_query_relationships_project_as_dict_with_descriptor_key(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).project({HasChild.nth_child: "child_num"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("child_num" in model for model in models)

        for model in models:
            assert 0 <= model["child_num"] <= 4

    def test_sync_client_query_relationships_project_as_dict_with_str_key(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).project({"nth_child": "child_num"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("child_num" in model for model in models)

        for model in models:
            assert 0 <= model["child_num"] <= 4

    def test_sync_client_query_relationships_project_as_model(self, sync_driver, seed_data):
        class Projection(BaseModel):
            nth_child: int

        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).project(Projection).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, Projection) for model in models)

        for model in models:
            assert 0 <= model.nth_child <= 4

    def test_sync_client_query_relationships_project_returns_unknown_keys_as_none(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = client.query(HasChild).project({"foobar": "my_foo"}).execute()
        assert isinstance(models, list)
        assert len(models) == 5
        assert all(isinstance(model, dict) for model in models)
        assert all("my_foo" in model for model in models)
        assert all(model["my_foo"] is None for model in models)

    def test_sync_client_query_relationships_project_overwrites_projection_if_called_multiple_times(
        self, sync_driver, seed_data
    ):
        client = Client(sync_driver)
        client.register(Adult, Child, HasChild)
        client.initialize()

        models = (
            client.query(HasChild)
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
