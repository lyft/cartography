import pytest

from cartography.intel.aws.util.common import parse_and_validate_aws_requested_syncs
# from cartography.intel.aws.util.common import get_account_from_arn


def test_parse_and_validate_requested_syncs():
    no_spaces = "ec2:instance,s3,rds,iam"
    assert parse_and_validate_aws_requested_syncs(no_spaces) == ['ec2:instance', 's3', 'rds', 'iam']

    mismatch_spaces = 'ec2:subnet, eks,kms'
    assert parse_and_validate_aws_requested_syncs(mismatch_spaces) == ['ec2:subnet', 'eks', 'kms']

    sync_that_does_not_exist = 'lambda_function, thisfuncdoesnotexist, route53'
    with pytest.raises(ValueError):
        parse_and_validate_aws_requested_syncs(sync_that_does_not_exist)

    absolute_garbage = '#@$@#RDFFHKjsdfkjsd,KDFJHW#@,'
    with pytest.raises(ValueError):
        parse_and_validate_aws_requested_syncs(absolute_garbage)


# def test_get_account_from_arn():
#     result = get_account_from_arn("arn:aws:iam::081157660428:role/TestRole")
#     assert result == "081157660428"
