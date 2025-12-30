import re
from typing import List, Optional

from neo4j import GraphDatabase
from pydantic import BaseModel

from loomi.clients.sync_client import LoomiClient
from loomi.models.node import LoomiNode
from loomi.query._state import LoomiQuery
from loomi.query.helpers import is_not_null


class Metadata(BaseModel):
    createdAt: str


class Tag(BaseModel):
    name: str


class Job(BaseModel):
    name: str
    level: int
    tags: List[Tag] = []


class Human(LoomiNode):
    name: str
    age: int
    metadata: Metadata
    jobs: List[Job]
    traits: List[str]


driver = GraphDatabase.driver("bolt://localhost:7688", auth=("memgraph", "password"))
client = LoomiClient(driver)

client.register(Human)


with client.session() as session:
    query = (
        LoomiQuery().match(Human, "h").where(is_not_null(Human.jobs.tags.all_().name)).returning()
    )
    # query = LoomiQuery().match(Human, "h").where(is_not_null(Human.jobs.all_().name)).returning()
    # query = LoomiQuery().match(Human, "h").where(is_not_null(Human.traits.any_())).returning()
    # query = LoomiQuery().match(Human, "h").where(is_not_null(Human.metadata.createdAt)).returning()
    # query = LoomiQuery().match(Human, "h").where(is_not_null(Human.name)).returning()

    result = session.run(*query)
    data = result.values()

pass

# a.b -> n0.a.b {{expr}}
# a.any_ -> ANY(i0 IN n0.a.b WHERE i0 {{expr}})
# a.any_.b -> ANY(i0 IN n0.a.b WHERE i0.b {{expr}})
# a.any_.b.all_ ANY(i0 IN n0.a.b WHERE ALL(i1 IN i0.b WHERE i1 {{expr}}))
# a.any_.b.all_.c ANY(i0 IN n0.a.b WHERE ALL(i1 IN i0.b WHERE i1.c {{expr}}))
