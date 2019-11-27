from cartography.intel.okta.awssaml import transform_okta_group_to_aws_role


def test_saml_with_default_regex():
    group_name = "aws#northamerica-production#Tier1_Support#828416469395"
    group_id = "groupid"
    default_regex = r"^aws\#\S+\#(?{{role}}[\w\-]+)\#(?{{accountid}}\d+)$"

    result = transform_okta_group_to_aws_role(group_id, group_name, default_regex)

    assert result
    assert result["groupid"] == group_id
    assert result["role"] == "arn:aws:iam::828416469395:role/Tier1_Support"


def test_saml_with_custom_regex():
    group_name = "AWS_123456789123_developer"
    group_id = "groupid"
    custom_regex = "AWS_(?{{accountid}}\\d+)_(?{{role}}[a-zA-Z0-9+=,.@\\-_]+)"

    result = transform_okta_group_to_aws_role(group_id, group_name, custom_regex)

    assert result
    assert result["groupid"] == group_id
    assert result["role"] == "arn:aws:iam::123456789123:role/developer"
