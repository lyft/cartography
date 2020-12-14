# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html
# https://docs.aws.amazon.com/STS/latest/APIReference/CommonErrors.html

from botocore.exceptions import ClientError
from boto3.session import Session

from libraries.kmslibrary import KMSLibrary
from utils.errors import classify_error


class AuthLibrary:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def session_duration(self):
        return self.config['aws']['sessionDuration']

    def get_assume_role_access_key(self):
        kms_helper = KMSLibrary(self.config['kms'], self.logger)
        return kms_helper.decrypt(self.config['kms']['assumeRoleAccessKeyCipher'])

    def get_assume_role_access_secret(self):
        kms_helper = KMSLibrary(self.config['kms'], self.logger)
        return kms_helper.decrypt(self.config['kms']['assumeRoleAccessSecretCipher'])

    def assume_role(self, args):
        # Create a Session with the credentials passed
        session = Session(
            aws_access_key_id=args['aws_access_key_id'],
            aws_secret_access_key=args['aws_secret_access_key']
        )

        try:
            sts_client = session.client(
                'sts',
                region_name=self.config['kms']['region']
            )
        except ClientError as e:
            raise classify_error(self.logger, e, 'Failed to create STS client')

        try:
            response = sts_client.assume_role(
                DurationSeconds=self.session_duration(),
                ExternalId=args['external_id'],
                RoleArn=args['role_arn'],
                RoleSessionName=args['role_session_name'],
            )

        except ClientError as e:
            raise classify_error(self.logger, e, 'Failed to assume role')

        return {
            'aws_access_key_id': response['Credentials']['AccessKeyId'],
            'aws_secret_access_key': response['Credentials']['SecretAccessKey'],
            'session_token': response['Credentials']['SessionToken'],
            # 'expiration': response['Credentials']['Expiration'],
        }

    def get_session(self, creds):
        # Create a Session with the credentials passed
        if creds['type'] == 'credentials':
            return Session(
                aws_access_key_id=creds['aws_access_key_id'],
                aws_secret_access_key=creds['aws_secret_access_key']
            )

        elif creds['type'] == 'assumerole':
            return Session(
                aws_access_key_id=creds['aws_access_key_id'],
                aws_secret_access_key=creds['aws_secret_access_key'],
                aws_session_token=creds['session_token']
            )
