# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable

import neo4j
import neo4j.graph
import pytest

from loomi._internal._change_tracker import TrackingOperation
from loomi._sync.client import Client
from loomi.graph.graph import Graph
from loomi.graph.node import Node
from loomi.graph.relationship import Relationship
from tests.fixtures.db import DriverSpec, driver_spec, sync_driver


class TestNativeResult:
    @pytest.mark.integration
    def test_keeps_original_records_from_peek(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.peek()
            assert data is not None
            assert isinstance(data[0], neo4j.graph.Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_keeps_original_records_from_fetch(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], neo4j.graph.Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_keeps_original_records_from_to_eager_result(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.to_eager_result()
            assert isinstance(data, neo4j.EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], neo4j.graph.Node)

            properties = dict(data.records[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_keeps_original_records_from_single(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.single()
            assert data is not None
            assert isinstance(data[0], neo4j.graph.Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_keeps_original_records_from_values(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], neo4j.graph.Node)

            properties = dict(data[0][0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_keeps_original_records_from_value(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.value()
            assert len(data) == 1
            assert isinstance(data[0], neo4j.graph.Node)

            properties = dict(data[0])
            assert "name" in properties
            assert properties["name"] == "John"

    @pytest.mark.integration
    def test_keeps_original_records_from_graph(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns the unchanged results."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("native") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.graph()
            assert isinstance(data, neo4j.graph.Graph)


class TestResult:
    @pytest.mark.integration
    def test_transforms_records_from_peek(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.peek()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    def test_transforms_records_from_peek_with_no_result(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method returns none if no results are returned."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"})

            data = result.peek()
            assert data is None

    @pytest.mark.integration
    def test_adds_records_from_peek_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            result.peek()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_fetch(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.fetch(1)
            assert len(data) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    @pytest.mark.integration
    def test_adds_records_from_fetch_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            result.fetch(1)
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_to_eager_result(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.to_eager_result()
            assert isinstance(data, neo4j.EagerResult)
            assert len(data.records) == 1
            assert isinstance(data.records[0][0], Human)
            assert data.records[0][0].name == "John"

    @pytest.mark.integration
    def test_adds_records_from_to_eager_result_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            result.to_eager_result()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_single(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.single()
            assert data is not None
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    def test_transforms_records_from_single_with_no_result(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) WHERE n.name = $name RETURN n", {"name": "James"})

            data = result.single()
            assert data is None

    @pytest.mark.integration
    def test_adds_records_from_single_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            result.single()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_values(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.values()
            assert len(data) == 1
            assert len(data[0]) == 1
            assert isinstance(data[0][0], Human)
            assert data[0][0].name == "John"

    @pytest.mark.integration
    def test_adds_records_from_values_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            result.values()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_value(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.value()
            assert len(data) == 1
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    def test_adds_records_from_value_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            result.value()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_graph(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.graph()
            assert isinstance(data, Graph)

    @pytest.mark.integration
    def test_adds_records_from_graph_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        class Likes(Relationship): ...

        with sync_driver.session() as session:
            session.run(
                "CREATE (:Human {name: $name1})-[r:LIKES]->(:Human {name: $name2})",
                {"name1": "John", "name2": "Jane"},
            )

        client = Client(sync_driver)
        client.register(Human, Likes)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run(
                "MATCH (n1:Human)-[r:LIKES]->(n2:Human) RETURN n1, r, n2", tracking=True
            )

            result.graph()
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 2
            assert (
                len(session.change_tracker._state[TrackingOperation.UPDATE]["relationships"].keys())
                == 1
            )

    @pytest.mark.integration
    def test_transforms_records_from_next(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = next(result)
            assert isinstance(data[0], Human)
            assert data[0].name == "John"

    @pytest.mark.integration
    def test_adds_records_from_next_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            next(result)
            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_transforms_records_from_iter(self, sync_driver: neo4j.Driver, driver_spec: DriverSpec):
        """Verify that the method transforms results to models."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            for data in result:
                assert isinstance(data[0], Human)
                assert data[0].name == "John"

    @pytest.mark.integration
    def test_adds_records_from_iter_to_change_tracker(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that the method adds results to the change tracker."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n", tracking=True)

            for _ in result:
                pass

            assert len(session.change_tracker._state[TrackingOperation.UPDATE]["nodes"].keys()) == 1

    @pytest.mark.integration
    def test_exposes_original_result_for_non_transformed_methods(
        self, sync_driver: neo4j.Driver, driver_spec: DriverSpec
    ):
        """Verify that other methods which do not return graph entities are still available."""

        class Human(Node):
            name: str

        with sync_driver.session() as session:
            session.run("CREATE (:Human {name: $name})", {"name": "John"})

        client = Client(sync_driver)
        client.register(Human)
        client.initialize()

        with client.session("loomi") as session:
            result = session.run("MATCH (n:Human) RETURN n")

            data = result.keys()
            assert isinstance(data, list)
            assert data == ["n"]
