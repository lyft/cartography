import neo4j

from tests.integration import settings


def test_neo4j_connection():
    driver = neo4j.GraphDatabase.driver(settings.get("NEO4J_URL"))
    with driver.session() as session:
        session.run("CALL db.schema();")
