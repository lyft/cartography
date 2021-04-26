import neo4j
import pytest
import neomodel

from tests.integration import settings


@pytest.fixture(scope="module")
def neo4j_session():
    neomodel.config.DATABASE_URL = 'bolt://neo4j:@localhost:7687'
    driver = neo4j.GraphDatabase.driver(settings.get("NEO4J_URL"))
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")
