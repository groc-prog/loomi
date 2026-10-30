# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

import pytest
from pydantic import BaseModel

from loomi.exceptions import ModelError
from loomi.graph.node import Node
from loomi.query_api._core.descriptors import FieldDescriptor


class TestNodeModelFields:
    def test_node_exposes_field_descriptors_on_class_field_paths(self):
        class Human(Node):
            name: str

        descriptor = Human.name
        assert isinstance(descriptor, FieldDescriptor)

    def test_node_raises_when_labels_not_available(self):
        class Human(Node): ...

        Human.loomi_config["labels"] = None  # type: ignore

        with pytest.raises(
            ModelError,
            match=f"Labels on model {Human.__name__} are not initialized. Maybe you forgot to call {Human.model_rebuild.__name__}?",
        ):
            Human.labels()


class TestNodeMagicMethods:
    def test_node_must_have_same_type_and_element_id_to_be_equal(self):
        class Human(Node): ...

        class Alien(Node): ...

        human1 = Human()
        human2 = Human()

        human3 = Human()
        human3._element_id = "4:ff04df25-ff2b-4b55-98f8-6888297b025e:0"

        human4 = Human()
        human4._element_id = "4:ff04df25-ff2b-4b55-98f8-6888297b025e:42"

        alien = Alien()

        assert human1 == human2
        assert (human1 == human3) is False
        assert (human3 == human4) is False
        assert (human1 == alien) is False


class TestNodeModelConfiguration:
    def test_node_uses_class_name_as_default_label(self):
        class Human(Node): ...

        assert "labels" in Human.loomi_config
        assert Human.loomi_config["labels"] == {Human.__name__}
        assert Human.labels() == {Human.__name__}

    def test_node_uses_defined_label(self):
        class Human(Node):
            loomi_config = {"labels": {"Worker", "Adult"}}

        assert "labels" in Human.loomi_config
        assert Human.loomi_config["labels"] == {"Worker", "Adult"}
        assert Human.labels() == {"Worker", "Adult"}

    def test_node_inherits_labels_from_parent_nodes(self):
        class Metadata(BaseModel): ...

        class Human(Node): ...

        class Adult(Node): ...

        class Worker(Human, Adult, Metadata): ...

        assert "labels" in Worker.loomi_config
        assert Worker.loomi_config["labels"] == {
            Human.__name__,
            Adult.__name__,
            Human.__name__,
            Worker.__name__,
        }
        assert Worker.labels() == {Human.__name__, Adult.__name__, Human.__name__, Worker.__name__}

    def test_node_inherits_labels_from_parent_node_and_defines_own_labels(self):
        class Human(Node): ...

        class Worker(Human):
            loomi_config = {"labels": {"FullTime", "Adult"}}

        assert "labels" in Worker.loomi_config
        assert Worker.loomi_config["labels"] == {Human.__name__, "FullTime", "Adult"}
        assert Worker.labels() == {Human.__name__, "FullTime", "Adult"}
