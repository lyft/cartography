## CleverCloud Configuration

.. _clevercloud_config:

Follow these steps to analyze CleverCloud objects with Cartography.

1. Prepare your CleverCloud OAuth secrets.
    1. Create a OAuth consumer in your CleverCloud console. See [CleverCloud Documentation](https://www.clever-cloud.com/doc/extend/cc-api/)
    1. CleverCloud ingest supports multiple organization by taking a base64-encoded config object structured as
        ```json
        [
             {
                 "consumer_key": "fakekey",
                 "consumer_secret": "fakesecret",
                 "client_key": "fakeclientkey",
                 "client_secret": "fakeclientsecret",
                 "org_id": "orga_f3b3bb57-db31-4dff-8708-0dd91cc31826"
             }
        ]
        ```    
    1. Base64 encode the auth object. You can encode the above sample in Python using
        ```python
        import json
        import base64
        auth_json = json.dumps([{"consumer_key": "fakekey","consumer_secret": "fakesecret","client_key": "fakeclientkey","client_secret":"fakeclientsecret","org_id": "orga_f3b3bb57-db31-4dff-8708-0dd91cc31826"}])
        base64.b64encode(auth_json.encode())
        ```
        and the resulting environment variable would be ```W3siY29uc3VtZXJfa2V5IjogImZha2VrZXkiLCAiY29uc3VtZXJfc2VjcmV0IjogImZha2VzZWNyZXQiLCAiY2xpZW50X2tleSI6ICJmYWtlY2xpZW50a2V5IiwgImNsaWVudF9zZWNyZXQiOiAiZmFrZWNsaWVudHNlY3JldCIsICJvcmdfaWQiOiAib3JnYV9mM2IzYmI1Ny1kYjMxLTRkZmYtODcwOC0wZGQ5MWNjMzE4MjYifV0=```
1. Populate an environment variable of your choice with the contents of the base64 output from the previous step.
1. Call the `cartography` CLI with `--clevercloud-config-env-var YOUR_ENV_VAR_HERE`.
1. `cartography` will then load your graph with data from all the organizations you specified.