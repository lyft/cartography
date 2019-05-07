import neo4j
import pytest

import cartography.intel.aws.iam
import tests.data.aws.iam


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


@pytest.fixture
def neo4j_session():
    driver = neo4j.GraphDatabase.driver("bolt://localhost:7687")
    with driver.session() as session:
        yield session
        session.run("MATCH (n) DETACH DELETE n;")


def test_load_roles(session):
    data = tests.data.aws.iam.LIST_ROLES['Roles']

    cartography.intel.aws.iam.load_roles(
        session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG
    )
