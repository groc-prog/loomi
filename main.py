from datetime import datetime
from typing import List, Set

import xxhash
from neo4j import GraphDatabase
from pydantic import BaseModel

from loomi.client.sync_client import LoomiClient
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship
from loomi.queries.alias import query_alias
from loomi.queries.builder import LoomiQuery


class Human(LoomiNode):
    name: str
    age: int
    metadata: "Metadata"
    items: list["Metadata"]


class Metadata(BaseModel):
    foo: str


class Likes(LoomiRelationship):
    pass


driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
client = LoomiClient(driver)

q = LoomiQuery().match(Human).match(query_alias(Likes, "l"), Human)

pass
