# pylint: disable=protected-access, missing-class-docstring, unused-variable, comparison-with-callable

from loomi.models.relationship import LoomiRelationship, LoomiRelationshipConfiguration


class TestLoomiRelationship:

    def test_default_type_is_class_name(self):
        """Verify that a relationship with no config uses its class name as the type."""

        class ActedIn(LoomiRelationship):
            pass

        assert "type" in ActedIn.loomi_config
        assert ActedIn.loomi_config["type"] == "ACTED_IN"

    def test_explicit_type_preserved(self):
        """Verify that providing an explicit type prevents the class name fallback."""

        class CustomRel(LoomiRelationship):
            loomi_config = LoomiRelationshipConfiguration(type="FOLLOWS")

        assert "type" in CustomRel.loomi_config
        assert CustomRel.loomi_config["type"] == "FOLLOWS"
        assert CustomRel.loomi_config["type"] != "CustomRel"

    def test_type_not_overwritten_by_parent(self):
        """
        Verify that the child's type is NOT merged or overwritten by the parent.
        In LoomiRelationship, 'type' is skipped during merging if already set.
        """

        class ParentRel(LoomiRelationship):
            loomi_config = LoomiRelationshipConfiguration(type="PARENT_TYPE")

        class ChildRel(ParentRel):
            loomi_config = LoomiRelationshipConfiguration(type="CHILD_TYPE")

        assert "type" in ChildRel.loomi_config
        assert ChildRel.loomi_config["type"] == "CHILD_TYPE"

    def test_config_inheritance_other_fields(self):
        """Verify that non-'type' config keys (like skip_indexes) are inherited."""

        class BaseRel(LoomiRelationship):
            loomi_config = LoomiRelationshipConfiguration(skip_indexes=True)

        class SubRel(BaseRel):
            pass

        assert "skip_indexes" in SubRel.loomi_config
        assert SubRel.loomi_config["skip_indexes"] is True
        assert "type" in SubRel.loomi_config
        assert SubRel.loomi_config["type"] == "SUB_REL"

    def test_instance_dirty_fields(self):
        """Verify that LoomiRelationship (via _LoomiBase) tracks attribute changes."""

        class MyRel(LoomiRelationship):
            since: int = 2020

        rel = MyRel()
        rel.since = 2024
        assert "since" in rel._dirty_fields

        rel.since = 2020
        assert "since" not in rel._dirty_fields
