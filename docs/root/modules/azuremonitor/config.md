## AzureMonitor Configuration

.. _azuremonitor_config:

Follow these steps to analyze Microsoft Azure Monitor (aka Azure Log Analytics or Microsoft Sentinel) with Cartography:

1. Set up an Azure identity for Cartography to use, and ensure that this identity has the built-in Azure [Microsoft Sentinel Reader role](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#microsoft-sentinel-reader) attached:
    * Authenticate: `$ az login`
    * Create a Service Principal: `$ az ad sp create-for-rbac --name cartography --role "Microsoft Sentinel Reader"`
    * Note the values of the `tenant`, `appId`, and `password` fields
1. Populate environment variables with the values generated in the previous step (e.g., `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`)
1. Call the `cartography` CLI with:
    ```bash
    --azuremonitor-workspace-name ALA_NAME \
    --azuremonitor-workspace-id ALA_GUID
    ```
