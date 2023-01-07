## Sumologic Configuration

.. _sumologic_config:

Follow these steps to collect Sumologic hosts data with Cartography:

1. Set up an Access key as per https://help.sumologic.com/docs/manage/security/access-keys/
1. Populate environment variable with the value generated in the previous step (for example, `SUMO_ACCESSKEY`)
1. Call the `cartography` CLI with:
    ```bash
    --sumologic-access-id xxx \
    --sumologic-access-key-env-var SUMO_ACCESSKEY \
    --sumologic-api-url https://api.us2.sumologic.com/api
    ```
    API url per https://help.sumologic.com/docs/api/getting-started/
