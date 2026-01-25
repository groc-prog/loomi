import time
from uuid import uuid4

from neo4j import GraphDatabase

from loomi.client.sync_client import LoomiClient

COUNT = 1000

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
client = LoomiClient(driver)
client.initialize()

start_default = time.perf_counter()
with client.session(mode="native") as session:
    with session.begin_transaction() as tx:
        for i in range(0, COUNT):
            tx.run("CREATE (n:Perf {uid: $uid})", {"uid": str(uuid4())})

end_default = time.perf_counter()

start_unwind = time.perf_counter()
with client.session(mode="native") as session:
    with session.begin_transaction() as tx:
        batch = []

        for i in range(0, COUNT):
            batch.append({"properties": {"uid": str(uuid4())}})

        tx.run("UNWIND $batch AS r CREATE (n:Perf) SET n = r.properties", {"batch": batch})

end_unwind = time.perf_counter()

print(f"WITHOUT UNWIND: {(end_default - start_default) * 100:.2f}ms")
print(f"WITH UNWIND: {(end_unwind - start_unwind) * 100:.2f}ms")
