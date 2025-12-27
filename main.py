from typing import Annotated

from neo4j import AsyncGraphDatabase, GraphDatabase

from loomi.client.sync_client import LoomiClient
from loomi.fields.annotations import UniquenessConstraint
from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

memgraph_driver = AsyncGraphDatabase.driver(
    "bolt://localhost:7688", auth=("memgraph", "password")
)


class Human(LoomiNode):
    uid: Annotated[str, UniquenessConstraint]


class Owns(LoomiRelationship):
    pass


c1 = LoomiClient(neo4j_driver)
c1._register_model(Human)
c1._register_model(Owns)


def do_cypher_tx(tx, cypher):
    result = tx.run(cypher)
    values = [record.values() for record in result]
    return values


with c1.session(True) as session:
    with session.begin_transaction() as tx:
        r1 = tx.run("MATCH (a)-[b]->(c) RETURN a, b, c")
        v1 = r1.values()


with c1.session(False) as session:
    with session.begin_transaction() as tx:
        r2 = tx.run("MATCH (a)-[b]->(c) RETURN a, b, c")
        v2 = r2.values()


pass
