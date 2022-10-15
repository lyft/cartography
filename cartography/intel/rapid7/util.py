"""
cartography/intel/rapid7/util
"""
# pylint: disable=invalid-name,broad-except
import json
import logging
import re
from array import array

import pandas
import requests

logger = logging.getLogger(__name__)


def extract_sub_from_resourceid(resourceid: str) -> str:
    """
    Get Azure subscription from Azure resource id
    """
    if isinstance(resourceid, str):
        try:
            sub = re.search(
                "/subscriptions/([0-9a-f-].*?)/resourceGroups/",
                resourceid,
                flags=re.IGNORECASE,
            ).group(1)
            return sub
        except AttributeError as exception:
            logging.exception("exception: %s", exception)
    return None


def extract_rg_from_resourceid(resourceid: str) -> str:
    """
    Get Azure subscription from Azure resource id
    """
    if isinstance(resourceid, str):
        try:
            rg = re.search(
                "/resourceGroups/(.*?)/providers/", resourceid, flags=re.IGNORECASE,
            ).group(1)
            return rg
        except AttributeError as exception:
            logging.exception("exception: %s", exception)
    return None


def extract_rapid7_configurations_subscriptionid(configurations):
    """
    Extract from json, specific keyvalue pair: azure subscription id

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return None

    subscription_id = None
    for line in configurations:
        if line["name"] == "azure":
            logger.warning("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            subscription_id = extract_sub_from_resourceid(azure["resourceId"])
            logger.warning(
                "extract_rapid7_configurations_subscriptionid0: %s (%s)",
                subscription_id,
                azure["resourceId"],
            )

    logger.warning("extract_rapid7_configurations_subscriptionid: %s", subscription_id)
    return subscription_id


def extract_rapid7_configurations_resourcegroup(configurations):
    """
    Extract from json, specific keyvalue pair: azure resource group

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return None

    rg = None
    for line in configurations:
        if line["name"] == "azure":
            logger.warning("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            rg = extract_rg_from_resourceid(azure["resourceId"])

    logger.warning("extract_rapid7_configurations_resourcegroup: %s", rg)
    return rg


def extract_rapid7_configurations_resourceid(configurations):
    """
    Extract from json, specific keyvalue pair: azure resource id

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return None

    resource_id = None
    for line in configurations:
        if line["name"] == "azure":
            logger.warning("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            resource_id = azure["resourceId"]

    logger.warning("extract_rapid7_configurations_resourceid: %s", resource_id)
    return resource_id


def extract_rapid7_configurations_instanceid(configurations):
    """
    Extract from json, specific keyvalue pair: azure instance id

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return None

    instance_id = None
    for line in configurations:
        if line["name"] == "azure":
            logger.warning("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            instance_id = azure["instanceId"]

    logger.warning("extract_rapid7_configurations_instanceid: %s", instance_id)
    return instance_id


def extract_rapid7_history_lastseen(history):
    """
    Extract from rapid7 history, last seen/scan time
    """
    lastseen = history[0]["date"]
    for entry in history:
        if lastseen < entry["date"]:
            lastseen = entry["date"]
    return lastseen


def extract_rapid7_history_firstseen(history):
    """
    Extract from rapid7 history, first seen/scan time
    """
    firstseen = history[0]["date"]
    for entry in history:
        if firstseen > entry["date"]:
            firstseen = entry["date"]
    return firstseen


# pylint: disable=too-many-arguments,too-many-locals
def Rapid7Hosts(
    authorization: tuple[str, str, str, bool],
    limit: int = 10000,
    page: int = 0,
    sort: str = "",
    nexpose_timeout: int = 5,
) -> array:
    """
    Get Nexpose inventory full data to array
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets

    To filter, use https://help.rapid7.com/insightvm/en-us/api/index.html#operation/findAssets

    Warning! if very large assets count (>10k, likely depending on assets details), it
    will have impact on memory needed for processing and could trigger linux oom-killer.
    Possible option: have the server generate a report and just retrieve it.
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/downloadReport
    """
    (
        nexpose_user,
        nexpose_password,
        nexpose_server_url,
        nexpose_verify_cert,
    ) = authorization
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
            "count %s, page %s, total_resources %s",
            count,
            page,
            total_resources,
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
                timeout=nexpose_timeout,
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

    logger.info("Flattening data")
    df_rapid7_tmp = pandas.json_normalize(result_array, sep="_", max_level=3)
    df_rapid7_tmp["subscription_id"] = df_rapid7_tmp["configurations"].apply(
        extract_rapid7_configurations_subscriptionid,
    )
    df_rapid7_tmp["resource_group"] = df_rapid7_tmp["configurations"].apply(
        extract_rapid7_configurations_resourcegroup,
    )
    df_rapid7_tmp["resource_id"] = df_rapid7_tmp["configurations"].apply(
        extract_rapid7_configurations_resourceid,
    )
    df_rapid7_tmp["instance_id"] = df_rapid7_tmp["configurations"].apply(
        extract_rapid7_configurations_instanceid,
    )
    df_rapid7_tmp["tool_last_seen"] = df_rapid7_tmp["history"].apply(
        extract_rapid7_history_lastseen,
    )
    df_rapid7_tmp["tool_first_seen"] = df_rapid7_tmp["history"].apply(
        extract_rapid7_history_firstseen,
    )
    logger.debug("Example df_rapid7_tmp: %s", df_rapid7_tmp.head(1))
    flatten_data = json.loads(df_rapid7_tmp.to_json(orient="records"))
    logger.debug("Example: %s", flatten_data[0])

    return flatten_data


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

    return ["TBD"]
