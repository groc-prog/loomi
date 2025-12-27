import datetime

from loomi.models.node import LoomiNode
from loomi.models.relationship import LoomiRelationship


class Human(LoomiNode):
    name: str
    age: int


class Animal(LoomiNode):
    name: str
    from_shelter: bool


class Owns(LoomiRelationship):
    since: datetime.datetime


class Loves(LoomiRelationship):
    very_much: bool
