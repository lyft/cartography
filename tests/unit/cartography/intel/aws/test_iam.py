from collections import namedtuple

from cartography.intel.aws import iam

SINGLE_STATEMENT = {
    "Resource": "*",
    "Action": "*",
}


def test__generate_policy_statements():
    statements = iam._generate_policy_statements(SINGLE_STATEMENT, "test_policy_id")
    assert True == isinstance(statements, list)
    assert True == isinstance(statements[0]["Action"], list)
    assert True == isinstance(statements[0]["Resource"], list)
    assert statements[0]["id"] == "test_policy_id/statement/1"
