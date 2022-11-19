"""
cartography/intel/rapid7/util
"""
import json
import logging
import re
from typing import Any
from typing import List
from typing import Tuple

import pandas
import requests

logger = logging.getLogger(__name__)


def extract_sub_from_resourceid(resourceid: str) -> str:
    """
    Get Azure subscription from Azure resource id
    """
    if isinstance(resourceid, str):
        match = re.search(
            "/subscriptions/([0-9a-f-].*?)/resourceGroups/",
            resourceid,
            flags=re.IGNORECASE,
        )
        if match:
            sub = match.group(1)
            return sub
    return ""


def extract_rg_from_resourceid(resourceid: str) -> str:
    """
    Get Azure subscription from Azure resource id
    """
    if isinstance(resourceid, str):
        match = re.search(
            "/resourceGroups/(.*?)/providers/",
            resourceid,
            flags=re.IGNORECASE,
        )
        if match:
            resource_group = match.group(1)
            return resource_group
    return ""


def extract_rapid7_configurations_subscriptionid(configurations: Any[str, list]) -> str:
    """
    Extract from json, specific keyvalue pair: azure subscription id

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return ""

    subscription_id = ""
    for line in configurations:
        if line["name"] == "azure":
            logger.debug("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            subscription_id = extract_sub_from_resourceid(azure["resourceId"])
            logger.debug(
                "extract_rapid7_configurations_subscriptionid0: %s (%s)",
                subscription_id,
                azure["resourceId"],
            )

    logger.debug("extract_rapid7_configurations_subscriptionid: %s", subscription_id)
    return subscription_id


def extract_rapid7_configurations_resourcegroup(configurations: Any[str, list]) -> str:
    """
    Extract from json, specific keyvalue pair: azure resource group

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return ""

    resource_group = ""
    for line in configurations:
        if line["name"] == "azure":
            logger.debug("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            resource_group = extract_rg_from_resourceid(azure["resourceId"])

    logger.debug("extract_rapid7_configurations_resourcegroup: %s", resource_group)
    return resource_group


def extract_rapid7_configurations_resourceid(configurations: Any[str, list]) -> str:
    """
    Extract from json, specific keyvalue pair: azure resource id

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return ""

    resource_id = ""
    for line in configurations:
        if line["name"] == "azure":
            logger.debug("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            resource_id = azure["resourceId"]

    logger.debug("extract_rapid7_configurations_resourceid: %s", resource_id)
    return resource_id


def extract_rapid7_configurations_instanceid(configurations: Any[str, list]) -> str:
    """
    Extract from json, specific keyvalue pair: azure instance id

    Input: dataframe row configurations column
    """

    if configurations is None or not isinstance(configurations, list):
        return ""

    instance_id = ""
    for line in configurations:
        if line["name"] == "azure":
            logger.debug("line: %s", line)
            if isinstance(line["value"], str):
                azure = json.loads(line["value"])
            else:
                azure = line["value"]
            instance_id = azure["instanceId"]

    logger.debug("extract_rapid7_configurations_instanceid: %s", instance_id)
    return instance_id


def rapid7_hosts(
    authorization: Tuple[str, str, str, bool],
    limit: int = 10000,
    page: int = 0,
    sort: str = "",
    nexpose_timeout: int = 5,
) -> List:
    """
    Get Nexpose inventory full data to array
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets

    To filter, use https://help.rapid7.com/insightvm/en-us/api/index.html#operation/findAssets

    Warning! if very large assets count (>10k, likely depending on assets details), it
    will have impact on memory needed for processing and could trigger linux oom-killer.
    Possible option: have the server generate a report and just retrieve it.
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/downloadReport
    """

    nexpose_verify_cert = authorization[3]
    logger.info("nexpose_verify_cert: %s", nexpose_verify_cert)
    if nexpose_verify_cert is not True:
        nexpose_verify_cert = False
        logger.warning("Requested to not verify certificate (%s)", nexpose_verify_cert)

    count = total_resources = 0
    size_interval = 500
    result_array: List[Any] = []
    while count < limit:
        logger.info(
            "count %s, page %s, total_resources %s",
            size_interval * page,
            page,
            total_resources,
        )
        # logger.debug("GetAssets params %s", params)
        try:
            resp = requests.get(
                f"{authorization[2]}/api/3/assets",
                headers={
                    "Content-type": "application/json",
                    "Accept": "application/json",
                },
                auth=(authorization[0], authorization[1]),
                verify=nexpose_verify_cert,
                params={  # type: ignore[arg-type]
                    "page": page,
                    "size": size_interval,
                    "sort": sort,
                },
                timeout=nexpose_timeout,
            )
            resp.raise_for_status()

            data = resp.json()

            if data["page"]["totalResources"] < limit:
                limit = data["page"]["totalResources"]

        except requests.HTTPError as exception:
            logger.exception("GetAssets0: %s", exception)
            return result_array

        if "resources" not in data:
            logger.warning("data without resources: %s", data)

        result_array = result_array + data["resources"]
        page += 1

    logger.debug("GetAssets final count %s", len(result_array))

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
        lambda x: min(entry["date"] for entry in x),
    )
    df_rapid7_tmp["tool_first_seen"] = df_rapid7_tmp["history"].apply(
        lambda x: max(entry["date"] for entry in x),
    )
    logger.debug("Example df_rapid7_tmp: %s", df_rapid7_tmp.head(1))
    flatten_data = json.loads(df_rapid7_tmp.to_json(orient="records"))
    logger.debug("Example: %s", flatten_data[0])

    return flatten_data
