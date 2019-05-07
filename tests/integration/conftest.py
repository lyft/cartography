import neo4j
import pytest


@pytest.fixture(scope="module")
def neo4j_session():
    driver = neo4j.GraphDatabase.driver("bolt://localhost:7687")
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")

