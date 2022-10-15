"""
cartography/intel/rapid7/util
"""
# pylint: disable=invalid-name,broad-except
import logging
from array import array
from typing import Any

import requests

logger = logging.getLogger(__name__)


# pylint: disable=too-many-arguments,too-many-locals
def Rapid7Hosts(
    authorization: tuple[str, str, str, bool],
    limit: int = 1000,
    page: int = 0,
    sort: str = "",
) -> array:
    """
    Get Nexpose inventory full data to array
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets

    To filter, use https://help.rapid7.com/insightvm/en-us/api/index.html#operation/findAssets
    """
    (nexpose_user, nexpose_password, nexpose_server_url, nexpose_verify_cert) = authorization
    url = nexpose_server_url + "/api/3/assets"
    headers = {"Content-type": "application/json", "Accept": "application/json"}

    logger.info("nexpose_verify_cert: %s", nexpose_verify_cert)
    if nexpose_verify_cert is not True:
        nexpose_verify_cert = False
        logger.warning("Requested to not verify certificate (%s)", nexpose_verify_cert)

    count = total_resources = 0
    size_interval = 500
    result_array = []
    while count < limit:
        logger.info(
            "count %s, page %s, total_resources %s", count, page, total_resources,
        )
        params = {"page": page, "size": size_interval, "sort": sort}
        # logger.debug("GetAssets params %s", params)
        try:
            resp = requests.get(
                url,
                headers=headers,
                auth=(nexpose_user, nexpose_password),
                verify=nexpose_verify_cert,
                params=params,
            )
            resp.raise_for_status()

            data = resp.json()

            total_resources = data["page"]["totalResources"]
            if total_resources < limit:
                limit = total_resources

        except requests.HTTPError as exception:
            logger.warning("GetAssets0: %s", resp.content)
            logger.exception("GetAssets0: %s", exception)
            return result_array

        try:
            if "resources" not in data:
                logger.warning("data without resources: %s", data)

        except Exception as exception:
            logger.warning("GetAssets1: %s", resp.content)
            logger.exception("GetAssets1 - Incomplete data: %s", exception)
            return result_array

        try:
            # logger.debug("GetAssets count %s", len(data['resources']))

            result_array = result_array + data["resources"]

            page += 1
            count += size_interval

        except Exception as exc:
            logger.warning("GetAssets3: %s", resp.content)
            logger.exception("GetAssets3 - Incomplete data: %s", exc)
            return result_array

    # logger.debug("result_array %s", (result_array))
    return result_array


# pylint: disable=unused-argument
def Rapid7VulnerabilitiesByHost(
    authorization: tuple[str, str, str, bool],
    machine_id,
) -> array:
    """
    Get Rapid7 vulnerabilities

    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getVulnerabilities
    Vulnerabilities per host are returned with hosts
    """

    # TBD

    return ['TBD']
