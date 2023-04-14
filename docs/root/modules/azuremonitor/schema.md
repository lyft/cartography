## AzureMonitor Schema

.. _azuremonitor_schema:

### AzureMonitor

Representation of a system sending logs to Azure Monitor aka Azure Log Analytics.

| Field | Description |
|-------|-------------|
|tool_first_seen| Timestamp of when first available logs for host is available since first sync|
|tool_last_seen| Timestamp of when last available logs for host is available per last sync|
|lastupdated| Timestamp of the last time the node was updated|
|**hostname**| The Azure Virtual Machine Computer name|
|short_hostname| The Azure Virtual Machine short hostname, lowercase|
|platform| The platform of the resource (linux or windows)|
|resource_group| The Resource Group where Virtual Machine is created|
|tenant_id| The Tenant Id where Virtual Machine is created|
|sentinel_sourcesystem| The SourceSystem as available in Log Analytics|
|sentinel_host_ip| The HostIP as available in Log Analytics|
|workspace_name| The Log Analytics workspace name where matching logs where identified|

#### Relationships

- Azure VirtualMachine contains one AzureMonitor host

        ```
        (VirtualMachine)-[PRESENT_IN]->(AzureMonitor)
        ```
