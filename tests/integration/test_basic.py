import neo4j


def test_neo4j_connection():
    driver = neo4j.GraphDatabase.driver("bolt://localhost:7687")
    with driver.session() as session:
        session.run("CALL db.schema();")
