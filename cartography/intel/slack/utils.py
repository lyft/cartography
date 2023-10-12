from typing import Any
from typing import Dict
from typing import List

from slack_sdk import WebClient


def slack_paginate(
    slack_client: WebClient,
    endpoint: str,
    data_key: str,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    endpoint_method = getattr(slack_client, endpoint)

    # First query
    response = endpoint_method(**kwargs)
    for item in response[data_key]:
        items.append(item)

    # Iterate over the cursor
    cursor = response.get('response_metadata', {}).get('next_cursor', '')
    while cursor != '':
        kwargs['cursor'] = cursor
        response = endpoint_method(**kwargs)
        for item in response[data_key]:
            items.append(item)
        cursor = response.get('response_metadata', {}).get('next_cursor', '')

    return items
