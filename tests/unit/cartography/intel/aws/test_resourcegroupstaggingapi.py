from cartography.intel.aws import resourcegroupstaggingapi as rgsa


def test_compute_resource_id():
    """
    Test that the id_func function pointer works correctly.
    """
    tag_mapping = {
        'ResourceARN': 'arn:aws:ec2:us-east-1:1234:instance/i-abcd',
        'Tags': [{
            'Key': 'my_key',
            'Value': 'my_value',
        }],
    }
    ec2_short_id = 'i-abcd'
    assert ec2_short_id == rgsa.compute_resource_id(tag_mapping, 'ec2:instance')
