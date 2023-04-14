## Azure Resource Graph Configuration

.. _azureresourcegraph_config:

Follow these steps to collect Azure Resource Graph data with Cartography:

### Service Principal setup

1. Set up an Azure identity for Cartography to use, and ensure that this identity has the built-in Azure [Microsoft Sentinel Reader role](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#microsoft-sentinel-reader) attached:
    * Authenticate: `$ az login`
    * Create a Service Principal: `$ az ad sp create-for-rbac --name cartography --role "Microsoft Sentinel Reader"`
    * Note the values of the `tenant`, `appId`, and `password` fields
1. Populate environment variables with the values generated in the previous step (e.g., `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`)
1. Call the `cartography` CLI with:
    ```bash
    --azureresourcegraph-tenant-id xxx \
    --azureresourcegraph-client-id-env-var  AZURE_CLIENT_ID \
    --azureresourcegraph-client-secret-env-var AZURE_CLIENT_SECRET
    ```

### Managed Identity setup

1. Call the `cartography` CLI with:
    ```bash
    --azureresourcegraph-tenant-id xxx \
    --azureresourcegraph-use-managedidentity
    ```
