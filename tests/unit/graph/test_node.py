# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

import json

from loomi.graph.node import Node


class TestNodeConfigMerge:
    def test_node_config_merges_labels(self):
        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
            }

        class Person(Human):
            loomi_config = {
                "labels": {"Person"},
            }

        assert "labels" in Person.loomi_config
        assert Person.loomi_config["labels"] == {"Human", "Person"}

    def test_node_config_inherits_serialization_functions(self):
        def serializer_fn(val):
            return ""

        def deserializer_fn(val):
            return ""

        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
                "serializer_fn": serializer_fn,
                "deserializer_fn": deserializer_fn,
            }

        class Person(Human):
            loomi_config = {
                "labels": {"Person"},
            }

        assert "serializer_fn" in Person.loomi_config
        assert Person.loomi_config["serializer_fn"] == serializer_fn
        assert "deserializer_fn" in Person.loomi_config
        assert Person.loomi_config["deserializer_fn"] == deserializer_fn

    def test_node_config_overrides_inherited_serialization_functions(self):
        def serializer_fn1(val):
            return ""

        def deserializer_fn1(val):
            return ""

        def serializer_fn2(val):
            return ""

        def deserializer_fn2(val):
            return ""

        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
                "serializer_fn": serializer_fn1,
                "deserializer_fn": deserializer_fn1,
            }

        class Person(Human):
            loomi_config = {
                "labels": {"Person"},
                "serializer_fn": serializer_fn2,
                "deserializer_fn": deserializer_fn2,
            }

        assert "serializer_fn" in Person.loomi_config
        assert Person.loomi_config["serializer_fn"] == serializer_fn2
        assert "deserializer_fn" in Person.loomi_config
        assert Person.loomi_config["deserializer_fn"] == deserializer_fn2

    def test_node_config_initializes_with_json_serializers(self):
        class Human(Node):
            loomi_config = {
                "labels": {"Human"},
            }

        assert "serializer_fn" in Human.loomi_config
        assert Human.loomi_config["serializer_fn"] == json.dumps
        assert "deserializer_fn" in Human.loomi_config
        assert Human.loomi_config["deserializer_fn"] == json.loads
