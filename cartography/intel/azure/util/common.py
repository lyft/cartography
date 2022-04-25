from typing import List

from cartography.intel.azure.resources import RESOURCE_FUNCTIONS


def parse_and_validate_azure_requested_syncs(azure_requested_syncs: str) -> List[str]:
    validated_resources: List[str] = []
    for resource in azure_requested_syncs.split(','):
        resource = resource.strip()

        if resource in RESOURCE_FUNCTIONS:
            validated_resources.append(resource)
        else:
            valid_syncs: str = ', '.join(RESOURCE_FUNCTIONS.keys())
            raise ValueError(
                f'Error parsing `azure-requested-syncs`. You specified "{azure_requested_syncs}". '
                f'Please check that your string is formatted properly. '
                f'Example valid input looks like "compute,sql,iam". '
                f'Our full list of valid values is: {valid_syncs}.',
            )
    return validated_resources
