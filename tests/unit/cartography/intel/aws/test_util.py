import pytest

from cartography.intel.aws.util.common import parse_and_validate_aws_custom_sync_profile
from cartography.intel.aws.util.common import parse_and_validate_aws_requested_syncs


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


def test_parse_and_validate_aws_custom_sync_profile():
    no_account_name = '{"aws_access_key_id": "efbg", "aws_secret_access_key": "abcd", "default_region": "abc"}'
    with pytest.raises(ValueError):
        parse_and_validate_aws_custom_sync_profile(no_account_name)

    valid = '{"account_name": "0", "aws_access_key_id": "1", "aws_secret_access_key": "2", "default_region": "3"}'
    assert parse_and_validate_aws_custom_sync_profile(valid) == {
        'account_name': '0',
        'aws_access_key_id': '1',
        'aws_secret_access_key': '2',
        'default_region': '3',
    }
