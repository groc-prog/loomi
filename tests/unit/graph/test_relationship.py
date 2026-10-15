# pylint: disable=missing-class-docstring, unused-import, redefined-outer-name, missing-function-docstring, unused-argument, line-too-long, unused-variable, comparison-with-callable

import json

from loomi.graph.relationship import Relationship


class TestRelationshipConfigMerge:
    def test_relationship_config_merges_type(self):
        class Likes(Relationship):
            loomi_config = {
                "type": "LIKES",
            }

        class Loves(Likes):
            loomi_config = {
                "type": "LOVES",
            }

        assert "type" in Loves.loomi_config
        assert Loves.loomi_config["type"] == "LOVES"

    def test_relationship_config_inherits_serialization_functions(self):
        def serializer_fn(val):
            return ""

        def deserializer_fn(val):
            return ""

        class Likes(Relationship):
            loomi_config = {
                "type": "LIKES",
                "serializer_fn": serializer_fn,
                "deserializer_fn": deserializer_fn,
            }

        class Loves(Likes):
            loomi_config = {
                "type": "LOVES",
            }

        assert "serializer_fn" in Loves.loomi_config
        assert Loves.loomi_config["serializer_fn"] == serializer_fn
        assert "deserializer_fn" in Loves.loomi_config
        assert Loves.loomi_config["deserializer_fn"] == deserializer_fn

    def test_relationship_config_overrides_inherited_serialization_functions(self):
        def serializer_fn1(val):
            return ""

        def deserializer_fn1(val):
            return ""

        def serializer_fn2(val):
            return ""

        def deserializer_fn2(val):
            return ""

        class Likes(Relationship):
            loomi_config = {
                "type": "LIKES",
                "serializer_fn": serializer_fn1,
                "deserializer_fn": deserializer_fn1,
            }

        class Loves(Likes):
            loomi_config = {
                "type": "LOVES",
                "serializer_fn": serializer_fn2,
                "deserializer_fn": deserializer_fn2,
            }

        assert "serializer_fn" in Loves.loomi_config
        assert Loves.loomi_config["serializer_fn"] == serializer_fn2
        assert "deserializer_fn" in Loves.loomi_config
        assert Loves.loomi_config["deserializer_fn"] == deserializer_fn2

    def test_relationship_config_initializes_with_json_serializers(self):
        class Likes(Relationship):
            loomi_config = {
                "type": "LIKES",
            }

        assert "serializer_fn" in Likes.loomi_config
        assert Likes.loomi_config["serializer_fn"] == json.dumps
        assert "deserializer_fn" in Likes.loomi_config
        assert Likes.loomi_config["deserializer_fn"] == json.loads
