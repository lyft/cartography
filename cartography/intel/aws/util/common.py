import json
from typing import Dict
from typing import List

from cartography.intel.aws.resources import RESOURCE_FUNCTIONS


def parse_and_validate_aws_requested_syncs(aws_requested_syncs: str) -> List[str]:
    validated_resources: List[str] = []
    for resource in aws_requested_syncs.split(','):
        resource = resource.strip()

        if resource in RESOURCE_FUNCTIONS:
            validated_resources.append(resource)
        else:
            valid_syncs: str = ', '.join(RESOURCE_FUNCTIONS.keys())
            raise ValueError(
                f'Error parsing `aws-requested-syncs`. You specified "{aws_requested_syncs}". '
                f'Please check that your string is formatted properly. '
                f'Example valid input looks like "s3,iam,rds" or "s3, ec2:instance, dynamodb". '
                f'Our full list of valid values is: {valid_syncs}.',
            )
    return validated_resources


def parse_and_validate_aws_custom_sync_profile(aws_custom_sync_profile: str) -> Dict[str, str]:
    aws_custom_sync_profile_dct = json.loads(aws_custom_sync_profile)
    for key in ['account_name', 'aws_access_key_id', 'aws_secret_access_key', 'default_region']:
        if key not in aws_custom_sync_profile_dct:
            raise ValueError(f'Error parsing aws_custom_sync_profile. No valid {key}.')
        value = aws_custom_sync_profile_dct[key]
        if type(value) != str or len(value) == 0:
            raise ValueError(
                f'Error parsing aws_custom_sync_profile. {key} should be a valid string.',
            )
    return aws_custom_sync_profile_dct
