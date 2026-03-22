from typing import List

from pydantic import BaseModel

from loomi.graph.node import Node
from loomi.query.functions import all_


class Item(BaseModel):
    name: str


class Human(Node):
    items: List[Item]


descriptor = all_(Human.items).name

pass
