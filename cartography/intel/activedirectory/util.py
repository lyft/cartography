"""
cartography/intel/activedirectory/util
"""
# pylint: disable=invalid-name,broad-except
import json
import logging
import os
from typing import Dict
from typing import List

import pandas

logger = logging.getLogger(__name__)


def activedirectory_hosts(
    authorization: tuple[str, str],
) -> List[Dict]:
    """
    Get ActiveDirectory (Logging) coverage inventory

    Loaded from json files produced by tool like SharpHound, BloodHound.py or RustHound
    """

    (
        activedirectory_dirpath,
        activedirectory_domain,
    ) = authorization
    activedirectory_filename = os.path.join(activedirectory_dirpath, "computers.json")
    if not (
        os.path.isdir(activedirectory_dirpath) and
        os.path.exists(activedirectory_filename)
    ):
        logger.warning(
            "Directory %s or matching computers.json don't exist",
            activedirectory_dirpath,
        )
        return {}

    with open(
        activedirectory_filename,
        encoding="utf-8",
    ) as data_file:
        data = json.load(data_file)

    df_computers = pandas.json_normalize(data["computers"], sep="_", max_level=3)
    logger.info("Example df_computers[0]: %s", df_computers.iloc[:1].to_string())
    logger.warning("Example df_computers[0]: %s", df_computers.iloc[:1].to_string())

    # df_computers["ad_domain"] = activedirectory_domain
    df_computers["ad_domain"] = df_computers["Properties_domain"]
    df_computers["hostname"] = df_computers["Properties_name"]
    df_computers["short_hostname"] = df_computers["hostname"].str.lower()
    df_computers["short_hostname"].replace(
        r"\..*$",
        "",
        regex=True,
        method="pad",
        inplace=True,
    )
    df_computers["objectid"] = df_computers["Properties_objectid"]
    df_computers["distinguishedname"] = df_computers["Properties_distinguishedname"]
    df_computers["highvalue"] = df_computers["Properties_highvalue"]
    df_computers["unconstraineddelegation"] = df_computers[
        "Properties_unconstraineddelegation"
    ]
    df_computers["enabled"] = df_computers["Properties_enabled"]

    df_computers.drop(
        columns=[
            "AllowedToAct",
            "LocalAdmins",
            "PSRemoteUsers",
            "RemoteDesktopUsers",
            "DcomUsers",
            "AllowedToDelegate",
            "Sessions",
            "Aces",
        ],
        inplace=True,
    )

    logger.info("activedirectoryHosts count final: %s", df_computers.shape[0])
    logger.warning("activedirectoryHosts count final: %s", df_computers.shape[0])

    # Rotate file to avoid importing same twice
    if os.access(activedirectory_filename, os.W_OK):
        logger.info("Moving %s to .old", activedirectory_filename)
        os.rename(activedirectory_filename, f"{activedirectory_filename}.old")

    if df_computers.shape[0]:
        flatten_data = json.loads(df_computers.to_json(orient="records"))
        logger.debug("Example: %s", flatten_data[0])
        logger.warning("Example: %s", flatten_data[0])
        return flatten_data

    logger.warning("No data returned")
    return {}
