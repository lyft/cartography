import cartography.intel.aws.iam
import tests.data.aws.iam


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_load_users(neo4j_session):
    data = tests.data.aws.iam.LIST_USERS['Users']

    cartography.intel.aws.iam.load_users(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_groups(neo4j_session):
    data = tests.data.aws.iam.LIST_GROUPS['Groups']

    cartography.intel.aws.iam.load_groups(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

def test_load_roles(neo4j_session):
    data = tests.data.aws.iam.LIST_ROLES['Roles']

    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_roles_creates_trust_relationships(neo4j_session):
    data = tests.data.aws.iam.LIST_ROLES['Roles']

    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Get TRUSTS_AWS_PRINCIPAL relationships from Neo4j.
    result = neo4j_session.run(
        """
        MATCH (n1:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(n2:AWSPrincipal) RETURN n1.arn, n2.arn;
        """
    )

    # Define the relationships we expect in terms of role ARN and principal ARN.
    expected = {
        ('arn:aws:iam::000000000000:role/example-role-0', 'arn:aws:iam::000000000000:root'),
        ('arn:aws:iam::000000000000:role/example-role-1', 'arn:aws:iam::000000000000:role/example-role-0'),
        ('arn:aws:iam::000000000000:role/example-role-2', 'ec2.amazonaws.com'),
        ('arn:aws:iam::000000000000:role/example-role-3', 'arn:aws:iam::000000000000:saml-provider/ADFS'),
    }
    # Transform the results of our query above to match the format of our expectations.
    actual = {
        (r['n1.arn'], r['n2.arn']) for r in result
    }
    # Compare our actual results to our expected results.
    assert actual == expected
