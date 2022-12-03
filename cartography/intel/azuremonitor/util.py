"""
cartography/intel/azuremonitor/util
"""
import datetime
import json
import logging
import os
from typing import List
from typing import Tuple

import pandas
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential
from azure.monitor.query import LogsQueryClient
from azure.monitor.query import LogsQueryStatus

logger = logging.getLogger(__name__)


def monitor_query(
    client: LogsQueryClient,
    workspace_id: str,
    query: str,
    start_time: datetime.date,
    end_time: datetime.date,
) -> pandas.DataFrame:
    """
    Azure Monitor Query

    https://pypi.org/project/azure-monitor-query/
    https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/monitor/azure-monitor-query
    https://learn.microsoft.com/en-us/python/api/overview/azure/monitor-query-readme?view=azure-python
    """
    try:
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=(start_time, end_time),
        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error.message)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            df_results = pandas.DataFrame(data=table.rows, columns=table.columns)
            return df_results
    except HttpResponseError as err:
        logger.exception("something fatal happened: %s", err)

    return pandas.DataFrame()


def azuremonitor_hosts(
    authorization: Tuple[str, str],
) -> List:
    """
    Get Azure Monitor/Sentinel (Logging) coverage inventory

    Timeout should be adapted to context, mostly size of indexes and searched timeperiod.
    Alternative: Msticpy
    https://msticpy.readthedocs.io/en/latest/data_acquisition/DataProv-MSSentinel.html#ms-sentinel-authentication-options
    """
    workspace_name = authorization[0]
    workspace_id = authorization[1]
    if "AZURE_CLIENT_ID" in os.environ:
        logger.info(
            "azuremonitor inputs: tenant %s, clientid %s, name %s",
            os.environ["AZURE_TENANT_ID"],
            os.environ["AZURE_CLIENT_ID"],
            workspace_name,
        )
    else:
        logger.info(
            "azuremonitor inputs: tenant %s, name %s - managed identity?",
            os.environ["AZURE_TENANT_ID"],
            workspace_name,
        )
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(hours=1)

    azure_token = ClientSecretCredential(
        os.environ["AZURE_TENANT_ID"],
        os.environ["AZURE_CLIENT_ID"],
        os.environ["AZURE_CLIENT_SECRET"],
    )
    logger.warning("Using App registration identity: %s", azure_token)
    client = LogsQueryClient(azure_token)

    syslog_query = (
        f"""search in (Syslog) "*"
| where TimeGenerated >= datetime({start_time})
| where TimeGenerated <= datetime({end_time})
| extend resource_group = extract("/resourcegroups/([0-9a-zA-Z.-]+)/providers/", 1, _ResourceId)
| summarize min(TimeGenerated), max(TimeGenerated) by Computer,_SubscriptionId,"""
        """resource_group,_ResourceId,TenantId,SourceSystem,HostIP
| extend firstseen = min_TimeGenerated, lastseen = max_TimeGenerated
| project-away min_TimeGenerated, max_TimeGenerated"""
    )
    df_syslog = monitor_query(client, workspace_id, syslog_query, start_time, end_time)
    df_syslog["systemtype"] = "linux"

    win_query = (
        f"""search in (Event, SecurityEvent) "*"
| where TimeGenerated >= datetime({start_time})
| where TimeGenerated <= datetime({end_time})
| extend resource_group = extract("/resourcegroups/([0-9a-zA-Z.-]+)/providers/", 1, _ResourceId)
| summarize min(TimeGenerated), max(TimeGenerated) by Computer,_SubscriptionId,"""
        """resource_group,_ResourceId,TenantId,SourceSystem
| extend firstseen = min_TimeGenerated, lastseen = max_TimeGenerated
| project-away min_TimeGenerated, max_TimeGenerated"""
    )
    df_win = monitor_query(client, workspace_id, win_query, start_time, end_time)
    df_win["systemtype"] = "windows"

    df_sentinel = pandas.concat([df_syslog, df_win])
    if workspace_name:
        df_sentinel["workspace_name"] = workspace_name

    logger.info("AzureMonitor count final: %s", df_sentinel.shape[0])

    df_sentinel["lastseen"] = pandas.to_datetime(
        df_sentinel["lastseen"],
        unit="s",
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")
    df_sentinel["firstseen"] = pandas.to_datetime(
        df_sentinel["firstseen"],
        unit="s",
    ).dt.strftime("%Y-%m-%dT%H:%M:%S")

    df_sentinel.rename(
        columns={
            "_SubscriptionId": "subscription_id",
            "_ResourceId": "resource_id",
        },
        errors="ignore",
        inplace=True,
    )
    if df_sentinel.shape[0]:
        flatten_data = json.loads(df_sentinel.to_json(orient="records"))
        logger.debug("Example: %s", flatten_data[0])
        return flatten_data

    logger.warning("No data returned")
    return []
