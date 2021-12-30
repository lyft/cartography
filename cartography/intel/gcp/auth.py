# https://google-auth.readthedocs.io/en/latest/user-guide.html#user-credentials
# https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.service_account.html#google.oauth2.service_account.Credentials
import uuid

import requests
from google.oauth2 import credentials


class AuthHelper:

    def get_credentials(self, token_uri: str, account_email: str) -> credentials.Credentials:
        try:
            session_string = str(uuid.uuid4())

            scopes = [
                "https://www.googleapis.com/auth/cloudplatformorganizations",
                "https://www.googleapis.com/auth/cloudplatformorganizations.readonly",
                "https://www.googleapis.com/auth/cloudplatformfolders",
                "https://www.googleapis.com/auth/cloudplatformfolders.readonly",
                "https://www.googleapis.com/auth/cloudplatformprojects",
                "https://www.googleapis.com/auth/cloudplatformprojects.readonly",
                "https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/cloud-platform.read-only",
                "https://www.googleapis.com/auth/iam",
            ]

            pload = {'sessionString': session_string, 'accountEmail': account_email, 'scopes': scopes}
            resp = requests.post(token_uri, json=pload)
            if resp.status_code == requests.codes['ok']:
                output = resp.json()

                return credentials.Credentials(output['accessToken'])

            else:
                print(f'failed while getting access token: {resp.status_code}')
                raise Exception(f'failed while getting access token: {resp.status_code}')

        except (ConnectionError, ConnectionRefusedError) as e:
            print(f'failed to connect to token generator: {str(e)}')
            raise Exception(f'{e}')

        except Exception as e:
            print(f'Failed while getting access token: {str(e)}')
            raise Exception(f'{e}')
