import logging
from typing import Dict
from typing import List

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def call_kandji_api(api_and_parameters: str, kandji_base_uri: str, kandji_token: str) -> List[Dict]:
    uri = kandji_base_uri + api_and_parameters
    try:
        response = requests.get(
            uri,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {kandji_token}',
            },
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning(f"Kandji: requests.get('{uri}') timed out.")
        raise
    # if call failed, use requests library to raise an exception
    response.raise_for_status()
    return response.json()
