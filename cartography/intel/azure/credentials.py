import logging
import requests
from datetime import datetime, timedelta

from azure.common.credentials import ServicePrincipalCredentials, get_azure_cli_credentials, get_cli_profile
from msrestazure.azure_active_directory import AADTokenCredentials
import adal


logger = logging.getLogger(__name__)
AUTHORITY_HOST_URI = 'https://login.microsoftonline.com'


class Authenticator:

    def authenticate_cli(self):
        """
        Implements authentication for the Azure provider
        """
        try:

            # Set logging level to error for libraries as otherwise generates a lot of warnings
            logging.getLogger('adal-python').setLevel(logging.ERROR)
            logging.getLogger('msrest').setLevel(logging.ERROR)
            logging.getLogger('msrestazure.azure_active_directory').setLevel(logging.ERROR)
            logging.getLogger('urllib3').setLevel(logging.ERROR)

            arm_credentials, subscription_id, tenant_id = get_azure_cli_credentials(with_tenant=True)
            aad_graph_credentials, placeholder_1, placeholder_2 = get_azure_cli_credentials(with_tenant=True, resource='https://graph.windows.net')

            profile = get_cli_profile()

            return Credentials(arm_credentials, aad_graph_credentials, tenant_id=tenant_id, current_user=profile.get_current_account_user(), subscription_id=subscription_id)

        except Exception as e:
            if ', AdalError: Unsupported wstrust endpoint version. ' \
                    'Current support version is wstrust2005 or wstrust13.' in e.args:
                raise Exception(
                    'You are likely authenticating with a Microsoft Account. '
                    'This authentication mode only support Azure Active Directory principal authentication.')

            raise Exception(e)

    def authenticate_sp(self, tenant_id=None, client_id=None, client_secret=None):
        """
        Implements authentication for the Azure provider
        """
        try:

            # Set logging level to error for libraries as otherwise generates a lot of warnings
            logging.getLogger('adal-python').setLevel(logging.ERROR)
            logging.getLogger('msrest').setLevel(logging.ERROR)
            logging.getLogger('msrestazure.azure_active_directory').setLevel(logging.ERROR)
            logging.getLogger('urllib3').setLevel(logging.ERROR)

            arm_credentials = ServicePrincipalCredentials(
                client_id=client_id,
                secret=client_secret,
                tenant=tenant_id
            )

            aad_graph_credentials = ServicePrincipalCredentials(
                client_id=client_id,
                secret=client_secret,
                tenant=tenant_id,
                resource='https://graph.windows.net'
            )

            profile = get_cli_profile()

            return Credentials(arm_credentials, aad_graph_credentials, tenant_id=tenant_id, current_user=profile.get_current_account_user())

        except Exception as e:
            if ', AdalError: Unsupported wstrust endpoint version. ' \
                    'Current support version is wstrust2005 or wstrust13.' in e.args:
                raise Exception(
                    'You are likely authenticating with a Microsoft Account. '
                    'This authentication mode only support Azure Active Directory principal authentication.')

            raise Exception(e)


class Credentials:

    def __init__(self, arm_credentials, aad_graph_credentials, tenant_id=None, subscription_id=None, context=None, current_user=None):

        self.arm_credentials = arm_credentials  # Azure Resource Manager API credentials
        self.aad_graph_credentials = aad_graph_credentials  # Azure AD Graph API credentials
        self.tenant_id = tenant_id
        self.subscription_id = subscription_id
        self.context = context
        self.current_user = current_user

    def get_current_user(self):
        return self.current_user

    def get_tenant_id(self):
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
            except Exception as e:
                logger.error('Unable to infer tenant ID: {}'.format(e))
                return None

    def get_credentials(self, resource):
        if resource == 'arm':
            self.arm_credentials = self.get_fresh_credentials(self.arm_credentials)
            return self.arm_credentials
        elif resource == 'aad_graph':
            self.aad_graph_credentials = self.get_fresh_credentials(self.aad_graph_credentials)
            return self.aad_graph_credentials
        else:
            raise Exception('Invalid credentials resource type')

    def get_fresh_credentials(self, credentials):
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

    def refresh_credential(self, credentials):
        """
        Refresh credentials
        """
        logger.debug('Refreshing credentials')
        authority_uri = AUTHORITY_HOST_URI + '/' + self.get_tenant_id()
        existing_cache = self.context.cache
        context = adal.AuthenticationContext(authority_uri, cache=existing_cache)
        new_token = context.acquire_token(credentials.token['resource'], credentials.token['user_id'], credentials.token['_client_id'])

        new_credentials = AADTokenCredentials(new_token, credentials.token.get('_client_id'))
        return new_credentials
