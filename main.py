from typing import Optional

from neo4j import GraphDatabase

from loomi._query._state import _InternalQueryState, _MatchQueryState, _StartQueryState
from loomi.clients.sync_client import LoomiClient
from loomi.models.node import LoomiNode


class Human(LoomiNode):
    name: Optional[str]
    age: int


class Animal(LoomiNode): ...


driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
client = LoomiClient(driver)

state = _InternalQueryState(client)
query = _StartQueryState(state)

query.match(Human, "h").match(Animal).set("h", {Human.name: "a", "age": 24}).returning()

pass

# MATCH (n.Human) RETURN n
# client.query(Human).returning()

# MATCH (n.Human) WHERE n.age > 24 RETURN n
# client.query(Human).where(gt(Human.age, 24)).returning()

# MATCH (n.Human) SET n.age = 24 RETURN n
# client.query(Human).set(Human.age, 24).returning()
# client.query(Human).set({"age": 24}).returning()
# client.query(Human).set({Human.age: 24}).returning()

# MATCH (n.Human) DETACH DELETE n RETURN n
# client.query(Human).detach_delete().returning()
