from cartography.intel.aws import iam

SINGLE_STATEMENT = {
    "Resource": "*",
    "Action": "*",
}


def test__generate_policy_statements():
    statements = iam._generate_policy_statements(SINGLE_STATEMENT, "test_policy_id")
    assert isinstance(statements, list)
    assert isinstance(statements[0]["Action"], list)
    assert isinstance(statements[0]["Resource"], list)
    assert statements[0]["id"] == "test_policy_id/statement/1"
