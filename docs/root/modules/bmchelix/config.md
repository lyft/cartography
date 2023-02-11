## BMC Helix Configuration

.. _bmchelix_config:

Follow these steps to collect BMC Helix data with Cartography:

1. Set up an Authentication token as per https://docs.bmc.com/docs/discovery/daas/authentication-and-permissions-in-the-rest-api-838557081.html
1. Populate environment variable with the value generated in the previous step (for example, `BMCHELIX_TOKEN`)
1. Call the `cartography` CLI with:
    ```bash
    --bmchelix-token-env-var BMCHELIX_TOKEN \
    --bmchelix-api-url https://INSTANCE.onbmc.com/api/v1.9
    ```
    API url per https://docs.bmc.com/docs/discovery/daas/using-the-rest-apis-838557075.html
