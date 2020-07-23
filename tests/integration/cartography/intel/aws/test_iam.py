import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
import tests.data.aws.iam

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _create_base_account(neo4j_session):
    neo4j_session.run("MERGE (a:AWSAccount{id:{AccountId}})", AccountId=TEST_ACCOUNT_ID)


def test_load_users(neo4j_session):
    _create_base_account(neo4j_session)
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
        """,
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


def test_load_inline_policy(neo4j_session):
    cartography.intel.aws.iam.load_policy(
        neo4j_session,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
        "group_inline_policy",
        "inline",
        "arn:aws:iam::000000000000:group/example-group-0",
        TEST_UPDATE_TAG,
    )


def test_load_inline_policy_data(neo4j_session):
    cartography.intel.aws.iam.load_policy_statements(
        neo4j_session,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
        "group_inline_policy",
        tests.data.aws.iam.INLINE_POLICY_STATEMENTS,
        TEST_UPDATE_TAG,
    )


def test_map_permissions(neo4j_session):
    # Insert an s3 bucket to map
    neo4j_session.run(
        """
    MERGE (s3:S3Bucket{arn:'arn:aws:s3:::test_bucket'})<-[:RESOURCE]-(a:AWSAccount{id:{AccountId}})
    """, AccountId=TEST_ACCOUNT_ID,
    )

    cartography.intel.aws.permission_relationships.sync(
        neo4j_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG, {
            "permission_relationships_file": "cartography/data/permission_relationships.yaml",
        },
    )
    results = neo4j_session.run("MATCH ()-[r:CAN_READ]->() RETURN count(r) as rel_count")
    assert results
    for result in results:
        assert result["rel_count"] == 1
