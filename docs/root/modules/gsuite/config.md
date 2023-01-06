## GSuite Configuration

.. _gsuite_config:

This module allows authentication from a service account or via oauth tokens.

1. Using service account (legacy)

    Ingesting GSuite Users and Groups utilizes the [Google Admin SDK](https://developers.google.com/admin-sdk/).

    1. [Enable Google API access](https://support.google.com/a/answer/60757?hl=en)
    1. Create a new G Suite user account and accept the Terms of Service. This account will be used as the domain-wide delegated access.
    1. [Perform G Suite Domain-Wide Delegation of Authority](https://developers.google.com/admin-sdk/directory/v1/guides/delegation)
    1.  Download the service account's credentials
    1.  Export the environmental variables:
        1. `GSUITE_GOOGLE_APPLICATION_CREDENTIALS` - location of the credentials file.
        1. `GSUITE_DELEGATED_ADMIN` - email address that you created in step 2

1. Using Oauth

    1. Create an App on [Google Cloud Console](https://console.cloud.google.com/)
    1. Refer to follow documentation if needed:
        1. https://developers.google.com/admin-sdk/directory/v1/quickstart/python
        1. https://developers.google.com/workspace/guides/get-started
        1. https://support.google.com/a/answer/7281227?hl=fr
    1. Download credentials file
    1. Use helper script for OAuth flow to obtain refresh_token
    1. Serialize needed secret
        ```
        import json
        import base64
        auth_json = json.dumps({"client_id":"xxxxx.apps.googleusercontent.com","client_secret":"ChangeMe", "refresh_token":"ChangeMe", "token_uri": "https://oauth2.googleapis.com/token"})
        base64.b64encode(auth_json.encode())
        ```
    1. Populate an environment variable of your choice with the contents of the base64 output from the previous step.
    1. Call the `cartography` CLI with `--gsuite-tokens-env-var YOUR_ENV_VAR_HERE` and `--gsuite-auth-method oauth`.




Google Oauth Helper :
```json
from __future__ import print_function
import json

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


scopes = ["https://www.googleapis.com/auth/admin.directory.userreadonly", "https://www.googleapis.com/auth/admin.directory.group.readonly", "https://www.googleapis.com/auth/admin.directory.group.member"]

print('Go to https://console.cloud.google.com/ > API & Services > Credentials and download secrets')
project_id = input('Provide your project ID:')
client_id = input('Provide you Client ID:')
client_secret = input('Provide you Client Secret:')
with open('credentials.json', 'w', encoding='utf-8') as fc:
    data = {
        "installed": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri":"https://accounts.google.com/o/oauth2/auth",
            "token_uri":"https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
            "client_secret":"client_secret",
            "redirect_uris":["http://localhost"]
        }}
    json.dump(data, fc)
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', scopes)
flow.redirect_uri = 'http://localhost'
auth_url, _ = flow.authorization_url(prompt='consent')
print(f'Please go to this URL: {auth_url}')
code = input('Enter the authorization code: ')
flow.fetch_token(code=code)
creds = flow.credentials
print('Testing your credentials by gettings first 10 users in the domain ...')
service = build('admin', 'directory_v1', credentials=creds)
print('Getting the first 10 users in the domain')
results = service.users().list(customer='my_customer', maxResults=10,
                                orderBy='email').execute()
users = results.get('users', [])
if not users:
    print('No users in the domain.')
else:
    print('Users:')
    for user in users:
        print(u'{0} ({1})'.format(user['primaryEmail'],
                                    user['name']['fullName']))
print('Your credentials:')
print(json.dumps(creds.to_json(), indent=2))
```
