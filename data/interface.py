import enum

from dotenv import load_dotenv
from neo4j import GraphDatabase
from os import environ as env

driver = GraphDatabase.driver(env['NEO4J_URI'], auth=(env['NEO4J_USER'], env['NEO4J_PASS']))


def __raw_add_user(tx, user_id, user_name):
    tx.run("CREATE (n:User {user_id: $user_id; user_name: $user_name})", user_id=user_id, user_name=user_name)


def add_user(user_id: int, user_name: str):
    with driver.session() as session:
        session.execute_write(__raw_add_user, user_id, user_name)
        driver.close()


class Relation(enum.Enum):
    Partner = "PARTNER_OF"
    Child = "CHILD_OF"

def __raw_add_relation(tx, user_id_l, user_id_r, relation):
    tx.run("MATCH (l:User {user_id: $user_id_l}), (r:User {user_id: $user_id_r}) "
           "MERGE (l)-[e:$relation]->(r) "
           "RETURN type(r)", user_id_l=user_id_l, user_id_r=user_id_r, relation=relation)


def add_relation(user_id_l: int, user_id_r: int, relation: Relation):
    with driver.session() as session:
        session.execute_write(__raw_add_relation, user_id_l, user_id_r, relation)
        driver.close()