# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

from loomi._async.client import AsyncClient
from tests.integration.utils.seed_data import Adult, Child, HasChild, seed_entities_async


class TestAsyncChangeTrackerAddsNodeResults:
    async def test_async_change_tracker_adds_node_results_from_peek(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.peek()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_fetch(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.fetch(1)

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_to_eager_result(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.to_eager_result()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_single(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.single()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_values(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.values()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_value(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.value()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_graph(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await result.graph()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_iter(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)

            async for record in result:
                record.values()

            add_spy.assert_called_once_with(adult)

    async def test_async_change_tracker_adds_node_results_from_next(self, async_driver, mocker):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        adult, *_ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH (a:Adult) RETURN a", tracking=True)
            await anext(result)

            add_spy.assert_called_once_with(adult)


class TestAsyncChangeTrackerAddsRelationshipResults:
    async def test_async_change_tracker_adds_relationship_results_from_peek(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.peek()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_fetch(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.fetch(1)

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_to_eager_result(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.to_eager_result()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_single(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.single()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_values(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.values()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_value(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.value()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_graph(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await result.graph()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_iter(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)

            async for record in result:
                record.values()

            add_spy.assert_called_once_with(has_child)

    async def test_async_change_tracker_adds_relationship_results_from_next(
        self, async_driver, mocker
    ):
        client = AsyncClient(async_driver)
        client.register(Adult, Child, HasChild)
        await client.initialize()

        _, has_child, _ = await seed_entities_async(async_driver)

        async with client.session() as session:
            add_spy = mocker.spy(session.change_tracker, "add")

            result = await session.run("MATCH ()-[a:HAS_CHILD]->() RETURN a", tracking=True)
            await anext(result)

            add_spy.assert_called_once_with(has_child)
