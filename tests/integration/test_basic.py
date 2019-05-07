from neo4j.v1 import GraphDatabase


def test_neo4j_connection():
    driver = GraphDatabase.driver("bolt://localhost:7687")
    with driver.session() as session:
        session.run("CALL db.schema();")
