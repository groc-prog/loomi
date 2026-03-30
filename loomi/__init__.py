# from neo4j import GraphDatabase

# neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
# memgraph_driver = GraphDatabase.driver("bolt://localhost:7688", auth=("memgraph", "password"))

# query = """
# RETURN trim('   hello   ')
# """
# parameters = {}

# with neo4j_driver.session() as neo4j_session:
#     neo4j_result = neo4j_session.run(query, parameters)
#     neo4j_value = neo4j_result.value()

# with memgraph_driver.session() as memgraph_session:
#     memgraph_result = memgraph_session.run(query, parameters)
#     memgraph_value = memgraph_result.value()

# pass


# from typing import Any

# from loomi.graph.node import Node
# from loomi.query.descriptor import PropertyDescriptor, _Descriptor


# class Human(Node): ...


# p = PropertyDescriptor("", Any, Human)
# a = isinstance(p, _Descriptor)

# pass


# """
# maybe wrap both parameter and property descriptor in dbfunctiondescriptor
# then in PropertyDescriptor check the type of parameter value and compile dbfunction template

# final part of query should be a placeholder and _compile_path in PropertyDescriptor should return
# a template and final part so that dbfunction can be applied later on. if no dbfunction defined, just
# compile template with final part only, otherwise compile dbfunction with final part first and then compile
# PropertyDescriptor tempalte with dbfunction compiled template

# tail
# abs
# ceil
# floor
# round
# toLower
# ltrim - (no 2. arg)
# rtrim - (no 2. arg)
# replace
# reverse
# left
# right
# split
# substring
# toUpper
# trim - (no 2. arg)
# """


# equals(to_lower(Human.name), "john")
