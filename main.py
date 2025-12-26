import pickle

from neo4j import AsyncGraphDatabase, GraphDatabase

from loomi.client.sync_client import LoomiClient
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

memgraph_driver = AsyncGraphDatabase.driver(
    "bolt://localhost:7688", auth=("memgraph", "password")
)


class Human(LoomiNode):
    uid: str


class Owns(LoomiRelationship):
    pass


c1 = LoomiClient(neo4j_driver)
c1._register_model(Human)
c1._register_model(Owns)

with c1.session(True) as session:
    # r1 = session.run("MATCH p=()-[]->() RETURN p")
    r1 = session.run("MATCH (a)-[b]->(c) RETURN a, b, c")
    # r1 = session.run("MATCH (n) RETURN n")
    v1 = r1.peek()

with c1.session(False) as session:
    # r2 = session.run("MATCH p=()-[]->() RETURN p")
    r2 = session.run("MATCH (a)-[b]->(c) RETURN a, b, c")
    # r2 = session.run("MATCH (n) RETURN n")
    v2 = r2.peek()

pass
