"""
cartography/intel/mde/util
"""
# pylint: disable=invalid-name,broad-except
import json
import logging
import re
import urllib.parse
import urllib.request
from array import array

import pandas
import requests

logger = logging.getLogger(__name__)


def get_authorization(
    client_id: str,
    client_secret: str,
    api_url: str,
    tenant_id: str,
) -> str:
    """
    Get Authentication token

    api_url: usually "https://api.securitycenter.microsoft.com"
    """
    # nosec - B105
    aad_token = ""
    try:
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"

        body = {
            "resource": api_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
        # logger.debug("auth body: %s", body)
        logger.debug("auth url: %s", url)

        data = urllib.parse.urlencode(body).encode("utf-8")

        req = urllib.request.Request(url, data)
        # nosemgrep
        response = urllib.request.urlopen(req)  # pylint: disable=consider-using-with
        json_response = json.loads(response.read())
        aad_token = json_response["access_token"]
        # logger.debug("aad_token: %s", json_response["access_token"])
    except TypeError as exc:
        logger.exception("Exception: %s", exc)

    return aad_token


def mde_hosts(
    authorization: str,
) -> array:
    """
    Get MDE assets inventory
    https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/get-machines?view=o365-worldwide
    """

    url = "https://api.securitycenter.microsoft.com/api/machines"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {authorization}",
    }
    # https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/exposed-apis-odata-samples?view=o365-worldwide
    params = {
        # '$stop': limit,
        "$skip": 0,
        # '$filter': "riskScore eq 'High'"
        # '$filter': "healthStatus ne 'Active'"
        # '$filter': "lastSeen gt 2018-08-01Z"
        # '$top': 100
    }
    logger.debug("headers: %s", headers)
    logger.debug("params: %s", params)

    # "$" may be required to not be encoded...
    # https://github.com/psf/requests/issues/1454#issuecomment-20832874
    qry = urllib.parse.urlencode(params).replace("%24", "$")
    sess = requests.Session()
    req = requests.Request(method="GET", headers=headers, url=url)
    prep = req.prepare()
    prep.url = url + "?" + qry
    resp = sess.send(prep)

    logger.debug("url: %s", resp.url)

    resp.raise_for_status()

    data = resp.json()

    full_data = []
    full_data += data["value"]
    j = 1
    while "@odata.nextLink" in data:
        logger.debug("@odata.nextLink present (%s): %s", j, data["@odata.nextLink"])
        try:
            resp2 = requests.get(data["@odata.nextLink"], headers=headers)
            resp2.raise_for_status()
            data = resp2.json()
            full_data += data["value"]
            logger.info("MdeHosts count: %s", len(full_data))
            j += 1
        except requests.HTTPError as exception:
            logger.exception("MdeHosts exception: %s", exception)

    logger.info("MdeHosts count final: %s", len(full_data))

    logger.info("Flattening data")
    df_mde_tmp = pandas.json_normalize(full_data, sep="_", max_level=3)
    # this makes easier comparison in neo4j
    df_mde_tmp["resource_group"] = df_mde_tmp["vmMetadata_resourceId"].apply(
        extract_rg_from_resourceid,
    )
    flatten_data = json.loads(df_mde_tmp.to_json(orient="records"))
    logger.debug("Example: %s", flatten_data[0])

    return flatten_data


def extract_rg_from_resourceid(resourceid: str) -> str:
    """
    Get Azure resource group from Azure resource id
    """
    if type(resourceid) is str:
        try:
            match = re.search(
                "/resourceGroups/(.*?)/providers/", resourceid, flags=re.IGNORECASE,
            )
            if match:
                rg = match.group(1)
                return rg
        except AttributeError as exception:
            logging.exception("exception: %s", exception)
    return ""
