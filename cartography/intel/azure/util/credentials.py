import base64
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional

import json
import logging
import requests
import time

import adal
from azure.core.credentials import AccessToken
from azure.common.credentials import get_azure_cli_credentials
from azure.common.credentials import get_cli_profile
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential
from msrestazure.azure_active_directory import AADTokenCredentials

logger = logging.getLogger(__name__)
AUTHORITY_HOST_URI = 'https://login.microsoftonline.com'


class Credentials:

    def __init__(
        self, arm_credentials: Any, aad_graph_credentials: Any, vault_credentials: Any, tenant_id: str = None, subscription_id: str = None,
        context: adal.AuthenticationContext = None, current_user: Dict = None,
    ) -> None:
        self.arm_credentials = arm_credentials  # Azure Resource Manager API credentials
        self.aad_graph_credentials = aad_graph_credentials  # Azure AD Graph API credentials
        self.vault_credentials = vault_credentials  # Azure vault API credentials
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.context = context
        self.current_user = current_user

    def get_current_user(self) -> Optional[str]:
        return self.current_user

    def get_tenant_id(self) -> Any:
        if self.tenant_id:
            return self.tenant_id
        elif 'tenant_id' in self.aad_graph_credentials.token:
            return self.aad_graph_credentials.token['tenant_id']
        else:
            # This is a last resort, e.g. for MSI authentication
            try:
                h = {'Authorization': 'Bearer {}'.format(self.arm_credentials.token['access_token'])}
                r = requests.get('https://management.azure.com/tenants?api-version=2020-01-01', headers=h)
                r2 = r.json()
                return r2.get('value')[0].get('tenantId')
            except requests.ConnectionError as e:
                logger.error(f'Unable to infer tenant ID: {e}')
                return None

    def get_credentials(self, resource: str) -> Any:
        if resource == 'arm':
            self.arm_credentials = self.get_fresh_credentials(self.arm_credentials)
            return self.arm_credentials
        elif resource == 'aad_graph':
            self.aad_graph_credentials = self.get_fresh_credentials(self.aad_graph_credentials)
            return self.aad_graph_credentials
        else:
            raise Exception('Invalid credentials resource type')

    def get_fresh_credentials(self, credentials: Any) -> Any:
        """
        Check if credentials are outdated and if so refresh them.
        """
        if self.context and hasattr(credentials, 'token'):
            expiration_datetime = datetime.fromtimestamp(credentials.token['expires_on'])
            current_datetime = datetime.now()
            expiration_delta = expiration_datetime - current_datetime
            if expiration_delta < timedelta(minutes=5):
                return self.refresh_credential(credentials)
        return credentials

    def refresh_credential(self, credentials: Any) -> Any:
        """
        Refresh credentials
        """
        logger.debug('Refreshing credentials')
        authority_uri = AUTHORITY_HOST_URI + '/' + self.get_tenant_id()
        if self.context:
            existing_cache = self.context.cache
            context = adal.AuthenticationContext(authority_uri, cache=existing_cache)

        else:
            context = adal.AuthenticationContext(authority_uri)

        new_token = context.acquire_token(
            credentials.token['resource'], credentials.token['user_id'], credentials.token['_client_id'],
        )

        new_credentials = AADTokenCredentials(new_token, credentials.token.get('_client_id'))
        return new_credentials


class ImpersonateCredentials(object):
    def __init__(self, cred: Credentials, resource: str) -> None:
        self.scheme = "Bearer"
        self.cred = cred
        self.resource = resource

    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        return AccessToken(self.cred['access_token'], int(self.cred['expires_in'] + time.time()))

    def signed_session(self, session=None):
        header = "{} {}".format(self.scheme, self.cred['access_token'])
        session.headers['Authorization'] = header
        return session


class Authenticator:

    def authenticate_cli(self) -> Credentials:
        """
        Implements authentication for the Azure provider
        """
        try:

            # Set logging level to error for libraries as otherwise generates a lot of warnings
            logging.getLogger('adal-python').setLevel(logging.ERROR)
            logging.getLogger('msrest').setLevel(logging.ERROR)
            logging.getLogger('msrestazure.azure_active_directory').setLevel(logging.ERROR)
            logging.getLogger('urllib3').setLevel(logging.ERROR)
            logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

            arm_credentials, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
            aad_graph_credentials, placeholder_1, placeholder_2 = get_azure_cli_credentials(
                with_tenant=True, resource='https://graph.windows.net',
            )

            profile = get_cli_profile()

            return Credentials(
                arm_credentials, aad_graph_credentials, tenant_id=tenant_id,
                current_user={'email': profile.get_current_account_user()}, subscription_id=subscription_id
            )

        except HttpResponseError as e:
            if ', AdalError: Unsupported wstrust endpoint version. ' \
                    'Current supported version is wstrust2005 or wstrust13.' in e.args:
                logger.error(
                    f'You are likely authenticating with a Microsoft Account. \
                    This authentication mode only supports Azure Active Directory principal authentication.\
                    {e}',
                )

            raise e

    def authenticate_sp(self, tenant_id: str = None, client_id: str = None, client_secret: str = None) -> Credentials:
        """
        Implements authentication for the Azure provider
        """
        try:

            # Set logging level to error for libraries as otherwise generates a lot of warnings
            logging.getLogger('adal-python').setLevel(logging.ERROR)
            logging.getLogger('msrest').setLevel(logging.ERROR)
            logging.getLogger('msrestazure.azure_active_directory').setLevel(logging.ERROR)
            logging.getLogger('urllib3').setLevel(logging.ERROR)
            logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

            arm_credentials = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
            )

            aad_graph_credentials = ClientSecretCredential(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                resource='https://graph.windows.net',
            )

            return Credentials(arm_credentials, aad_graph_credentials, tenant_id=tenant_id, current_user=client_id)
            # return Credentials(
            #     arm_credentials, aad_graph_credentials, tenant_id=tenant_id, current_user={'email': profile.get_current_account_user()}
            # )

        except HttpResponseError as e:
            if ', AdalError: Unsupported wstrust endpoint version. ' \
                    'Current supported version is wstrust2005 or wstrust13.' in e.args:
                logger.error(
                    f'You are likely authenticating with a Microsoft Account. \
                    This authentication mode only supports Azure Active Directory principal authentication.\
                    {e}',
                )

            raise e

    # vault_scope: https://vault.azure.net/user_impersonation
    def impersonate_user(self, client_id: str, client_secret: str, redirect_uri: str, refresh_token: str, graph_scope: str, azure_scope: str, vault_scope: str, subscription_id: str):
        """
        Implements Impersonation authentication for the Azure provider
        """

        # Set logging level to error for libraries as otherwise generates a lot of warnings
        logging.getLogger('adal-python').setLevel(logging.ERROR)
        logging.getLogger('msrest').setLevel(logging.ERROR)
        logging.getLogger('msrestazure.azure_active_directory').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

        try:
            graph_creds = self.refresh_graph_token(client_id, client_secret, redirect_uri, refresh_token, graph_scope)
            vault_creds = self.refresh_vault_token(client_id, client_secret, redirect_uri, refresh_token, vault_scope)
            azure_creds = self.refresh_azure_token(client_id, client_secret, redirect_uri, refresh_token, azure_scope)
            tenant_id, user = self.decode_jwt(azure_creds.cred['id_token'])

            return Credentials(azure_creds, graph_creds, vault_creds, subscription_id=subscription_id, tenant_id=tenant_id, current_user=user)

        except Exception as e:
            logging.info(f'failed to impersonate user: {str(e)}')

            raise Exception(e)

    def refresh_graph_token(self, client_id: str, client_secret: str, redirect_uri: str, refresh_token: str, scope: str) -> ImpersonateCredentials:
        return ImpersonateCredentials(self.get_access_token(client_id, client_secret, redirect_uri, refresh_token, scope), "graph")

    def refresh_vault_token(self, client_id, client_secret, redirect_uri, refresh_token, scope):
        return ImpersonateCredentials(self.get_access_token(client_id, client_secret, redirect_uri, refresh_token, scope), "vault")

    def refresh_azure_token(self, client_id: str, client_secret: str, redirect_uri: str, refresh_token: str, scope: str) -> ImpersonateCredentials:
        return ImpersonateCredentials(self.get_access_token(client_id, client_secret, redirect_uri, refresh_token, scope), "management")

    def get_access_token(self, client_id: str, client_secret: str, redirect_uri: str, refresh_token: str, scope: str) -> Dict:
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        grant_type = "refresh_token"
        content_type = "application/x-www-form-urlencoded"
        headers = {"Content-Type": content_type}

        pload = f'grant_type={grant_type}&scope={scope}&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}&refresh_token={refresh_token}'
        r = requests.post(token_url, data=pload, headers=headers)
        return r.json()

    def decode_jwt(self, id_token: str) -> Dict:
        payload = id_token.split('.')[1]

        # Standard Base64 Decoding
        decodedBytes = base64.b64decode(payload + '===')
        decodedStr = str(decodedBytes.decode('utf-8'))

        # print(decodedStr)

        decoded = json.loads(decodedStr)
        # print('tenant id', decoded['tid'])
        # print('user id', decoded['oid'])
        # print('name', decoded['name'])
        # print('email', decoded['preferred_username'])

        return decoded['tid'], {
            'id': decoded['oid'],
            'name': decoded['name'],
            'email': decoded['preferred_username']
        }
