import copy

import cartography.intel.aws.resourcegroupstaggingapi as rgta
import tests.data.aws.resourcegroupstaggingapi as test_data


def test_compute_resource_id():
    """
    Test that the id_func function pointer behaves as expected and returns the instanceid from an EC2Instance's ARN.
    """
    tag_mapping = {
        'ResourceARN': 'arn:aws:ec2:us-east-1:1234:instance/i-abcd',
        'Tags': [{
            'Key': 'my_key',
            'Value': 'my_value',
        }],
    }
    ec2_short_id = 'i-abcd'
    assert ec2_short_id == rgta.compute_resource_id(tag_mapping, 'ec2:instance')


def test_get_bucket_name_from_arn():
    arn = 'arn:aws:s3:::bucket_name'
    assert 'bucket_name' == rgta.get_bucket_name_from_arn(arn)


def test_get_short_id_from_ec2_arn():
    arn = 'arn:aws:ec2:us-east-1:test_account:instance/i-1337'
    assert 'i-1337' == rgta.get_short_id_from_ec2_arn(arn)


def test_get_short_id_from_elb_arn():
    arn = 'arn:aws:elasticloadbalancing:::loadbalancer/foo'
    assert 'foo' == rgta.get_short_id_from_elb_arn(arn)


def test_get_short_id_from_lb2_arn():
    arn = 'arn:aws:elasticloadbalancing:::loadbalancer/app/foo/abdc123'
    assert 'foo' == rgta.get_short_id_from_lb2_arn(arn)


def test_transform_tags():
    get_resources_response = copy.deepcopy(test_data.GET_RESOURCES_RESPONSE)
    assert 'resource_id' not in get_resources_response[0]
    rgta.transform_tags(get_resources_response, 'ec2:instance')
    assert 'resource_id' in get_resources_response[0]
