from typing import Any, List

from cartography.intel.aws.resources import RESOURCE_FUNCTIONS, RESOURCE_IDENTIFIERS


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

def _get_resource_identifier(aws_resource_type: str) -> str: 
  return RESOURCE_IDENTIFIERS[aws_resource_type]

def filter_resources(data: List[Any], aws_resource_name: str, aws_resource_type: str) -> List[Any]:
    filtered = []
    if aws_resource_type == 's3':
        for bucket in data['Buckets']: # type: ignore
              if aws_resource_name == bucket['Name']:
                  filtered.append(bucket)
                  break
        data['Buckets'] = filtered # type: ignore
        return data
    elif aws_resource_type == 'dynamodb':
        for table in data:
            if table["Table"]["TableName"] == aws_resource_name:
                filtered.append(table)
                break
        return filtered
    else:
      for resource in data:
          if resource[_get_resource_identifier(aws_resource_type)] == aws_resource_name :
              filtered.append(resource)
              break
    
    return filtered