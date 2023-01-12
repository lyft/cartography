## Hexnode Configuration

.. _hexnode_config:

Follow these steps to analyze Hexnode objects with Cartography.

1. Prepare your Hexnode API key.
    1. Generate your API token by following the steps from Hexnode [Generating API Keys documentation](https://www.hexnode.com/mobile-device-management/developers/setting-up-an-api/retrieve-api-key/)
    1. Get your tenant ID from your dashboard URL `https://{TENANT_ID}.hexnodemdm.com`
    1. Populate an environment variable with the API key. You can pass the environment variable name via CLI with the `--hexnode-api-key-env-var` parameter.
    1. Pass the tenant name via CLI with the `--hexnode-tenant` parameter.
