# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import neo4j
import neo4j.graph
import pytest

from loomi._async.client import AsyncClient
from loomi._internal._change_tracker import TrackingOperation
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from tests.fixtures.db import DriverSpec, async_driver, driver_spec


class TestNativeAsyncResult:
    @pytest.mark.integration
    async def test_keeps_original_records_from_peek(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.peek()
            assert data is not None
            assert isinstance(data[0], neo4j.graph.Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    async def test_keeps_original_records_from_fetch(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], neo4j.graph.Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    async def test_keeps_original_records_from_to_eager_result(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.to_eager_result()
            assert isinstance(data, neo4j.EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], neo4j.graph.Node)

            properties = dict(data.records[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    async def test_keeps_original_records_from_single(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.single()
            assert data is not None
            assert isinstance(data[0], neo4j.graph.Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    async def test_keeps_original_records_from_values(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], neo4j.graph.Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    async def test_keeps_original_records_from_value(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.value()
            assert len(data) == 1
            assert isinstance(data[0], neo4j.graph.Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    async def test_keeps_original_records_from_graph(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("native") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.graph()
            assert isinstance(data, neo4j.graph.Graph)


class TestAsyncResult:
    @pytest.mark.integration
    async def test_transforms_records_from_peek(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.peek()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    async def test_transforms_records_from_peek_with_no_result(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method returns none if no results are returned."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"}
            )

            data = await result.peek()
            assert data is None

    @pytest.mark.integration
    async def test_adds_records_from_peek_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await result.peek()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_fetch(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    @pytest.mark.integration
    async def test_adds_records_from_fetch_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await result.fetch(1)
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_to_eager_result(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.to_eager_result()
            assert isinstance(data, neo4j.EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], Human)
            assert data.records[0][0].name == "John"

    @pytest.mark.integration
    async def test_adds_records_from_to_eager_result_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await result.to_eager_result()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_single(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.single()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    async def test_transforms_records_from_single_with_no_result(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"}
            )

            data = await result.single()
            assert data is None

    @pytest.mark.integration
    async def test_adds_records_from_single_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await result.single()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_values(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    @pytest.mark.integration
    async def test_adds_records_from_values_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await result.values()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_value(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.value()
            assert len(data) == 1
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    async def test_adds_records_from_value_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await result.value()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_graph(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await result.graph()
            assert isinstance(data, Graph)

    @pytest.mark.integration
    async def test_adds_records_from_graph_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        class Likes(Relationship): ...

        async with async_driver.session() as session:
            await session.run(
                "CREATE (:Human {name: $name1})-[r:LIKES]->(:Human {name: $name2})",
                {"name1": "John", "name2": "Jane"},
            )

        client = AsyncClient(async_driver)
        client.register(Human, Likes)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run(
                "MATCH (n1:Human)-[r:LIKES]->(n2:Human) RETURN n1, r, n2", tracking=True
            )

            await result.graph()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 2
            assert (
                len(session.change_tracker._state[TrackingOperation.UPDATE]["relationships"].keys())
                == 1
            )

    @pytest.mark.integration
    async def test_transforms_records_from_next(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = await anext(result)
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    async def test_adds_records_from_next_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            await anext(result)
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_transforms_records_from_iter(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            async for data in result:
                assert isinstance(data[0], Human)
                assert data[0].name == "John"

    @pytest.mark.integration
    async def test_adds_records_from_iter_to_change_tracker(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n", tracking=True)

            async for _ in result:
                pass

            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    async def test_exposes_original_result_for_non_transformed_methods(
        self, async_driver: neo4j.AsyncDriver, driver_spec: DriverSpec
    ):
        """Verify that other methods which do not return graph entities are still available."""

        class Human(Node):
            name: str

        async with async_driver.session() as session:
            await session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = AsyncClient(async_driver)
        client.register(Human)
        await client.initialize()

        async with client.session("loomi") as session:
            result = await session.run("MATCH (n:Human) RETURN n")

            data = result.keys()
            assert isinstance(data, list)
            assert data == ["n"]
