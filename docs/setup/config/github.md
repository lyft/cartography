<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Github Configuration](#github-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Github Configuration

Follow these steps to analyze Github repos and other objects with Cartography.

1. Prepare your Github credentials.
    1. Github ingest supports multiple endpoints, such as a public instance and an enterprise instance by taking a base64-encoded config object structured as
        ```json
       {
        "organization": [
            {
                "token": "faketoken",
                "url": "https://api.github.com/graphql",
                "name": "fakeorg"
            },
            {
                "token": "stillfake",
                "url": "https://github.example.com/api/graphql",
                "name": "fakeorg"
            }]
       }
       ```
    1. For each Github instance you want to ingest, generate an API token as documented in the [API reference](https://developer.github.com/v3/auth/)
    1. Create your auth config as shown above using the token obtained in the previous step. If you are configuring only the public Github instance, you can just use the first config block and delete the second. The name field is for the organization name you want to ingest.
    1. Base64 encode the auth object and populate an environment variable with the result. For example, you could encode the above sample in Python using
       ```python
       import json
       import base64
       str = json.dumps({"organization":[{"token":"faketoken","url":"https://api.github.com/graphql","name":"fakeorg"},{"token":"stillfake","url":"https://github.example.com/api/graphql","name":"fakeorg"}]})
       base64.b64encode(str.encode())
       ```
       and the resulting environment variable would be ```eyJvcmdhbml6YXRpb24iOiBbeyJ0b2tlbiI6ICJmYWtldG9rZW4iLCAidXJsIjogImh0dHBzOi8vYXBpLmdpdGh1Yi5jb20vZ3JhcGhxbCIsICJuYW1lIjogImZha2VvcmcifSwgeyJ0b2tlbiI6ICJzdGlsbGZha2UiLCAidXJsIjogImh0dHBzOi8vZ2l0aHViLmV4YW1wbGUuY29tL2FwaS9ncmFwaHFsIiwgIm5hbWUiOiAiZmFrZW9yZyJ9XX0=```
