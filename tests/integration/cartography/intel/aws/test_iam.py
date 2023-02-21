import copy

import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
import tests.data.aws.iam
from cartography.cli import CLI
from cartography.config import Config
from cartography.sync import build_default_sync

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def test_permission_relationships_file_arguments():
    """
    Test that we correctly read arguments for --permission-relationships-file
    """
    # Test the correct field is set in the Cartography config object
    fname = '/some/test/file.yaml'
    config = Config(
        neo4j_uri='bolt://thisdoesnotmatter:1234',
        permission_relationships_file=fname,
    )
    assert config.permission_relationships_file == fname

    # Test the correct field is set in the Cartography CLI object
    argv = ['--permission-relationships-file', '/some/test/file.yaml']
    cli_object = CLI(build_default_sync(), prog='cartography')
    cli_parsed_output = cli_object.parser.parse_args(argv)
    assert cli_parsed_output.permission_relationships_file == '/some/test/file.yaml'

    # Test that the default RPR file is set if --permission-relationships-file is not set in the CLI
    argv = []
    cli_object = CLI(build_default_sync(), prog='cartography')
    cli_parsed_output = cli_object.parser.parse_args(argv)
    assert cli_parsed_output.permission_relationships_file == 'cartography/data/permission_relationships.yaml'


def _create_base_account(neo4j_session):
    neo4j_session.run("MERGE (a:AWSAccount{id:$AccountId})", AccountId=TEST_ACCOUNT_ID)


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
        TEST_ACCOUNT_ID,
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


def test_load_server_certificates(neo4j_session):
    data = copy.deepcopy(tests.data.aws.iam.LIST_SERVER_CERTIFICATES)
    cartography.intel.aws.iam.load_server_certificates(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("arn:aws:iam::123456789012:server-certificate/myUpdatedServerCertificate", 1571203396),
        ("arn:aws:iam::123456789012:server-certificate/Org1/Org2/MyTestCert", 1515981156),
    }
    nodes = neo4j_session.run(
        """
        MATCH (sc:ServerCertificate) RETURN sc.id as id, sc.expiration as expiration;
        """,
    )
    actual_nodes = {(n['id'], n['expiration']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_credential_report_users(neo4j_session):
    data = copy.deepcopy(tests.data.aws.iam.CREDENTIAL_REPORT_CONTENT)
    credential_report_users = cartography.intel.aws.iam.transform_credential_report_users(data)
    cartography.intel.aws.iam.load_credential_report_users(
        neo4j_session,
        credential_report_users,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        ("arn:aws:iam::000000000000:root", None),
        ("arn:aws:iam::000000000000:user/user1", 1659361910),
        ("arn:aws:iam::000000000000:user/user2", 1661944234),
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:CredentialReportUser) RETURN n.arn as arn, n.access_key_1_last_rotated as access_key_1_last_rotated;
        """,
    )
    actual_nodes = {(n['arn'], n['access_key_1_last_rotated']) for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_account_password_policy(neo4j_session):
    data = copy.deepcopy(tests.data.aws.iam.ACCOUNT_PASSWORD_POLICY)
    cartography.intel.aws.iam.load_account_password_policy(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected_nodes = {
        ("000000000000", False, 90),
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:AccountPasswordPolicy) RETURN n.id as id, n.expire_passwords as e, n.max_password_age as m;
        """,
    )
    actual_nodes = {(n['id'], n['e'], n['m']) for n in nodes}
    assert actual_nodes == expected_nodes
