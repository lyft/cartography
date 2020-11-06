from cartography.intel.aws import iam

SINGLE_STATEMENT = {
    "Resource": "*",
    "Action": "*",
}

# Example principal field in an AWS policy statement
# see: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
SINGLE_PRINCIPAL = {
    "AWS": "test-role-1",
    "Service": ["test-service-1", "test-service-2"],
    "Federated": "test-provider-1",
}


def test__generate_policy_statements():
    statements = iam._transform_policy_statements(SINGLE_STATEMENT, "test_policy_id")
    assert isinstance(statements, list)
    assert isinstance(statements[0]["Action"], list)
    assert isinstance(statements[0]["Resource"], list)
    assert statements[0]["id"] == "test_policy_id/statement/1"


def test__parse_principal_entries():
    principal_entries = iam._parse_principal_entries(SINGLE_PRINCIPAL)
    assert isinstance(principal_entries, list)
    assert len(principal_entries) == 4
    assert principal_entries[0] == ("AWS", "test-role-1")
    assert principal_entries[1] == ("Service", "test-service-1")
    assert principal_entries[2] == ("Service", "test-service-2")
    assert principal_entries[3] == ("Federated", "test-provider-1")
