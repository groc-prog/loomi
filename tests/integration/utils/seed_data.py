from loomi.graph.node import Node
from loomi.graph.relationship import Relationship


class Adult(Node):
    name: str
    age: int

    loomi_config = {"labels": {"Adult"}}


class Child(Node):
    name: str

    loomi_config = {"labels": {"Child"}}


class HasChild(Relationship):
    nth_child: int
    tag: str

    loomi_config = {"type": "HAS_CHILD"}


def seed_start_and_end_nodes_sync(driver):
    with driver.session() as session:
        result = session.run(
            "CREATE (a:Adult $a), (c:Child $c) RETURN a, c",
            {
                "a": {"name": "John", "age": 21},
                "c": {"name": "Jimmy"},
            },
        )
        values = result.values()
        assert len(values) == 1
        assert len(values[0]) == 2

        created_adult = values[0][0]
        created_child = values[0][1]

        adult = Adult(name=created_adult["name"], age=created_adult["age"])
        adult._element_id = created_adult.element_id
        adult._id = created_adult.id

        child = Child(name=created_child["name"])
        child._element_id = created_child.element_id
        child._id = created_child.id

    return adult, child


def seed_entities_sync(driver):
    with driver.session() as session:
        result = session.run(
            "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c) RETURN a, b, c",
            {
                "a": {"name": "John", "age": 21},
                "b": {"nth_child": 1, "tag": "oldest"},
                "c": {"name": "Jimmy"},
            },
        )
        values = result.values()
        assert len(values) == 1
        assert len(values[0]) == 3

        created_adult = values[0][0]
        created_has_child = values[0][1]
        created_child = values[0][2]

        adult = Adult(name=created_adult["name"], age=created_adult["age"])
        adult._element_id = created_adult.element_id
        adult._id = created_adult.id

        has_child = HasChild(tag=created_has_child["tag"], nth_child=created_has_child["nth_child"])
        has_child._element_id = created_has_child.element_id
        has_child._id = created_has_child.id

        child = Child(name=created_child["name"])
        child._element_id = created_child.element_id
        child._id = created_child.id

    return adult, has_child, child


async def seed_start_and_end_nodes_async(driver):
    async with driver.session() as session:
        result = await session.run(
            "CREATE (a:Adult $a), (c:Child $c) RETURN a, c",
            {
                "a": {"name": "John", "age": 21},
                "c": {"name": "Jimmy"},
            },
        )
        values = await result.values()
        assert len(values) == 1
        assert len(values[0]) == 2

        created_adult = values[0][0]
        created_child = values[0][1]

        adult = Adult(name=created_adult["name"], age=created_adult["age"])
        adult._element_id = created_adult.element_id
        adult._id = created_adult.id

        child = Child(name=created_child["name"])
        child._element_id = created_child.element_id
        child._id = created_child.id

    return adult, child


async def seed_entities_async(driver):
    async with driver.session() as session:
        result = await session.run(
            "CREATE (a:Adult $a)-[b:HAS_CHILD $b]->(c:Child $c) RETURN a, b, c",
            {
                "a": {"name": "John", "age": 21},
                "b": {"nth_child": 1, "tag": "oldest"},
                "c": {"name": "Jimmy"},
            },
        )
        values = await result.values()
        assert len(values) == 1
        assert len(values[0]) == 3

        created_adult = values[0][0]
        created_has_child = values[0][1]
        created_child = values[0][2]

        adult = Adult(name=created_adult["name"], age=created_adult["age"])
        adult._element_id = created_adult.element_id
        adult._id = created_adult.id

        has_child = HasChild(tag=created_has_child["tag"], nth_child=created_has_child["nth_child"])
        has_child._element_id = created_has_child.element_id
        has_child._id = created_has_child.id

        child = Child(name=created_child["name"])
        child._element_id = created_child.element_id
        child._id = created_child.id

    return adult, has_child, child
