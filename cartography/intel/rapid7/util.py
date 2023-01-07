"""
cartography/intel/rapid7/util
"""
import json
import logging
import os
import re
from io import StringIO
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


def extract_rapid7_configurations_subscriptionid(configurations: Any[str, List]) -> str:
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


def extract_rapid7_configurations_resourcegroup(configurations: Any[str, List]) -> str:
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


def extract_rapid7_configurations_resourceid(configurations: Any[str, List]) -> str:
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


def extract_rapid7_configurations_instanceid(configurations: Any[str, List]) -> str:
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


def rapid7_hosts_from_getassets(
    authorization: Tuple[str, str, str, str, str, int],
    limit: int = 6000,
    page: int = 0,
    # examples: "id,ASC", "id,DESC"
    sort: str = "",
    nexpose_timeout: int = 60,
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
    if nexpose_verify_cert.lower() != "true":
        nexpose_verify_cert2 = False
        logger.warning("Requested to not verify certificate (%s)", nexpose_verify_cert)
    else:
        nexpose_verify_cert2 = True

    count = total_resources = 0
    size_interval = 500
    result_array: List[Any] = []
    df_rapid7_tmp = pandas.DataFrame()
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
                verify=nexpose_verify_cert2,
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


def rapid7_hosts_from_downloadreport(
    authorization: Tuple[str, str, str, str, str, int],
    nexpose_timeout: int = 60,
) -> List:
    """
    Get Nexpose inventory full data to array
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/downloadReport
    https://docs.rapid7.com/nexpose/sql-query-export-examples/
    """

    nexpose_verify_cert = authorization[3]
    logger.info("nexpose_verify_cert: %s", nexpose_verify_cert)
    if nexpose_verify_cert.lower() != "true":
        nexpose_verify_cert2 = False
        logger.warning("Requested to not verify certificate (%s)", nexpose_verify_cert)
    else:
        nexpose_verify_cert2 = True

    if int(authorization[5]) < 0:
        # Fetch accessible reports
        resp0 = requests.get(
            f"{authorization[2]}/api/3/reports/",
            headers={
                "Content-type": "application/json",
                "Accept": "application/json",
            },
            auth=(authorization[0], authorization[1]),
            verify=nexpose_verify_cert2,
            timeout=nexpose_timeout,
        )
        resp0.raise_for_status()

        data0 = resp0.content
        logger.info("Accessible rapid7 reports: %s", data0)
    else:
        resp = requests.get(
            f"{authorization[2]}/api/3/reports/{authorization[5]}/history/latest/output",
            headers={
                "Content-type": "application/json",
                "Accept": "application/json",
            },
            auth=(authorization[0], authorization[1]),
            verify=nexpose_verify_cert,
            timeout=nexpose_timeout,
        )
        resp.raise_for_status()

        # https://requests.readthedocs.io/en/latest/user/quickstart/#binary-response-content
        # The gzip and deflate transfer-encodings are automatically decoded for you.
        data = resp.content

    if data:
        logger.debug("Data[:1000]: %s", data[:1000])
        df_rapid7_tmp = pandas.read_csv(
            StringIO(data.decode("utf-8")),
            encoding="utf8",
            sep=",",
        )
        df_rapid7_tmp.rename(
            columns={
                "asset_id": "id",
                "ip_address": "r7_ip",
                "mac_address": "r7_mac",
                "host_name": "hostName",
                "vulnerabilities": "vulnerabilities_total",
                "critical_vulnerabilities": "vulnerabilities_critical",
                "moderate_vulnerabilities": "vulnerabilities_moderate",
                # "vulnerability_instances": ?
                "riskscore": "riskScore",
                "vendor": "osFingerprint_product",
                "version": "osFingerprint_version",
                "unique_id": "instance_id",
                "last_assessed_for_vulnerabilities": "tool_last_seen",
            },
            errors="ignore",
            inplace=True,
        )
        df_rapid7_tmp["short_hostname"] = df_rapid7_tmp["hostName"].str.lower()
        df_rapid7_tmp["short_hostname"].replace(r"\..*$", "", regex=True, inplace=True)
        df_rapid7_tmp["tool_last_seen"] = pandas.to_datetime(
            df_rapid7_tmp["tool_last_seen"],
            format="%Y-%m-%d %H:%M:%S.%f",
        ).dt.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info("downloadReport final count %s", df_rapid7_tmp.shape[0])
        logger.debug("Example df_rapid7_tmp: %s", df_rapid7_tmp.head(1))
        flatten_data = json.loads(df_rapid7_tmp.to_json(orient="records"))
        logger.debug("Example: %s", flatten_data[0])

        return flatten_data

    return []


def rapid7_hosts_from_reportfile(
    authorization: Tuple[str, str, str, str, str, int],
) -> List:
    """
    Get Nexpose inventory full data to array

    From local csv file already extracted from Rapid7
    """

    rapid7_dirpath = authorization[4]
    rapid7_filename = os.path.join(rapid7_dirpath, "rapid7.csv")
    if not (os.path.isdir(rapid7_dirpath) and os.path.exists(rapid7_filename)):
        logger.warning(
            "Directory %s or matching rapid7.csv don't exist",
            rapid7_dirpath,
        )
        return []

    # expected columns:
    # asset_id, mac_address, ip_address, host_name, operating_system, sites,
    # last_assessed_for_vulnerabilities, scan_started, scan_finished, vulnerabilities,
    # critical_vulnerabilities, moderate_vulnerabilities, vulnerability_instances,
    # riskscore, pci_status, asset_type, description, vendor, family, name, version,
    # architecture, system, cpe, source, unique_id
    df_rapid7_tmp = pandas.read_csv(rapid7_filename)

    # keep same naming than with API
    df_rapid7_tmp.rename(
        columns={
            "asset_id": "id",
            "ip_address": "r7_ip",
            "mac_address": "r7_mac",
            "host_name": "hostName",
            "vulnerabilities": "vulnerabilities_total",
            "critical_vulnerabilities": "vulnerabilities_critical",
            "moderate_vulnerabilities": "vulnerabilities_moderate",
            # "vulnerability_instances": ?
            "riskscore": "riskScore",
            "vendor": "osFingerprint_product",
            "version": "osFingerprint_version",
            "unique_id": "instance_id",
            "last_assessed_for_vulnerabilities": "tool_last_seen",
        },
        errors="ignore",
        inplace=True,
    )

    df_rapid7_tmp["short_hostname"] = df_rapid7_tmp["hostName"].str.lower()
    df_rapid7_tmp["short_hostname"].replace(r"\..*$", "", regex=True, inplace=True)
    df_rapid7_tmp["tool_last_seen"] = pandas.to_datetime(
        df_rapid7_tmp["tool_last_seen"],
        format="%Y-%m-%d %H:%M:%S.%f",
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")

    logger.info("Rapid7Hosts count final: %s", df_rapid7_tmp.shape[0])

    # Rotate file to avoid importing same twice
    if os.access(rapid7_filename, os.W_OK):
        logger.info("Moving %s to .old", rapid7_filename)
        os.rename(rapid7_filename, f"{rapid7_filename}.old")

    if df_rapid7_tmp.shape[0]:
        flatten_data = json.loads(df_rapid7_tmp.to_json(orient="records"))
        logger.debug("Example: %s", flatten_data[0])
        return flatten_data

    logger.warning("No data returned")
    return []


# pylint: disable=too-many-arguments,too-many-locals
def rapid7_hosts(
    authorization: Tuple[str, str, str, str, str, int],
    limit: int = 6000,
    page: int = 0,
    # examples: "id,ASC", "id,DESC"
    sort: str = "",
    nexpose_timeout: int = 60,
) -> List:
    """
    Get Nexpose inventory full data to array
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/getAssets

    To filter, use https://help.rapid7.com/insightvm/en-us/api/index.html#operation/findAssets

    Warning! if very large assets count (>10k, likely depending on assets details), it
    will have impact on memory needed for processing and could trigger linux oom-killer.
    Possible option: have the server generate a report and just retrieve it.
    https://help.rapid7.com/insightvm/en-us/api/index.html#operation/downloadReport
    Even w 48GB RAM, only up to 13k...
    """

    if authorization[2] and authorization[4]:
        return rapid7_hosts_from_reportfile(authorization)
    if authorization[2] and authorization[5]:
        return rapid7_hosts_from_downloadreport(authorization)

    return rapid7_hosts_from_getassets(
        authorization,
        limit,
        page,
        sort,
        nexpose_timeout,
    )
