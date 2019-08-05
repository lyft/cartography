import neo4j
import pytest

from tests.integration import settings


@pytest.fixture(scope="module")
def neo4j_session():
    driver = neo4j.GraphDatabase.driver(settings.get("NEO4J_URL"))
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
