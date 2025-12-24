# pylint: disable=protected-access, missing-class-docstring, unused-variable, comparison-with-callable

from loomi.models.node import LoomiNode, LoomiNodeConfiguration


class TestLoomiNode:

    def test_default_label_is_class_name(self):
        """Verify that a node with no config uses its class name as the default label."""

        class UserNode(LoomiNode):
            pass

        assert "labels" in UserNode.loomi_config
        assert "UserNode" in UserNode.loomi_config["labels"]
        assert len(UserNode.loomi_config["labels"]) == 1

    def test_explicit_labels_preserved(self):
        """Verify that providing explicit labels prevents the class name fallback."""

        class CustomNode(LoomiNode):
            loomi_config = LoomiNodeConfiguration(labels={"CustomLabel"})

        assert "labels" in CustomNode.loomi_config
        assert "CustomLabel" in CustomNode.loomi_config["labels"]
        assert "CustomNode" not in CustomNode.loomi_config["labels"]

    def test_label_inheritance_merging(self):
        """Verify that child nodes merge their labels with parent nodes."""

        class ParentNode(LoomiNode):
            loomi_config = LoomiNodeConfiguration(labels={"Parent"})

        class ChildNode(ParentNode):
            loomi_config = LoomiNodeConfiguration(labels={"Child"})

        assert "labels" in ChildNode.loomi_config
        assert ChildNode.loomi_config["labels"] == {"Parent", "Child"}

    def test_multi_level_inheritance(self):
        """Verify labels accumulate across multiple levels of inheritance."""

        class GrandParent(LoomiNode):
            loomi_config = LoomiNodeConfiguration(labels={"GP"})

        class Parent(GrandParent):
            loomi_config = LoomiNodeConfiguration(labels={"P"})

        class Child(Parent):
            loomi_config = LoomiNodeConfiguration(labels={"C"})

        assert "labels" in Child.loomi_config
        assert Child.loomi_config["labels"] == {"GP", "P", "C"}

    def test_dirty_fields_tracking(self):
        """Verify that setting attributes adds them to the _dirty_fields set."""

        class DataNode(LoomiNode):
            name: str = "default"

        node = DataNode()
        node.name = "updated"
        assert "name" in node._dirty_fields

        node.name = "default"
        assert "name" not in node._dirty_fields

    def test_id_and_element_id_computed_fields(self):
        """Verify that private IDs are correctly exposed via computed properties."""

        class IdNode(LoomiNode):
            pass

        node = IdNode()
        node._id = 123
        node._element_id = "uuid-abc"

        assert node.id == 123
        assert node.element_id == "uuid-abc"
