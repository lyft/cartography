# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html
# https://docs.aws.amazon.com/STS/latest/APIReference/CommonErrors.html
from boto3.session import Session
from neo4j.exceptions import ClientError

from libraries.kmslibrary import KMSLibrary
from utils.errors import classify_error


class AuthLibrary:
    def __init__(self, context):
        self.context = context

    def get_assume_role_access_key(self):
        kms_helper = KMSLibrary(self.context)
        return kms_helper.decrypt(self.context.assume_role_access_key_cipher)

    def get_assume_role_access_secret(self):
        kms_helper = KMSLibrary(self.context)
        return kms_helper.decrypt(self.context.assume_role_access_secret_cipher)

    def assume_role(self, args):
        # Create a Session with the credentials passed
        session = Session(
            aws_access_key_id=args['aws_access_key_id'],
            aws_secret_access_key=args['aws_secret_access_key'],
        )

        try:
            sts_client = session.client(
                'sts',
                region_name=self.context.region,
            )
        except ClientError as e:
            raise classify_error(self.context.logger, e, 'Failed to create STS client')

        try:
            response = sts_client.assume_role(
                ExternalId=args['external_id'],
                RoleArn=args['role_arn'],
                RoleSessionName=args['role_session_name'],
                DurationSeconds=3600*4,
            )

        except ClientError as e:
            try:
                response = sts_client.assume_role(
                    ExternalId=args['external_id'],
                    RoleArn=args['role_arn'],
                    RoleSessionName=args['role_session_name'],
                    DurationSeconds=3600,
                )

            except ClientError as e:
                # TODO: Check if the error is related to Duration, if yes, retry with 1 hour
                raise classify_error(self.context.logger, e, 'Failed to assume role')

        return {
            'aws_access_key_id': response['Credentials']['AccessKeyId'],
            'aws_secret_access_key': response['Credentials']['SecretAccessKey'],
            'session_token': response['Credentials']['SessionToken'],
            'expiration': response['Credentials']['Expiration'],
        }

    def get_session(self, creds):
        # Create a Session with the credentials passed
        if creds['type'] == 'credentials':
            return Session(
                aws_access_key_id=creds['aws_access_key_id'],
                aws_secret_access_key=creds['aws_secret_access_key'],
            )

        elif creds['type'] == 'assumerole':
            return Session(
                aws_access_key_id=creds['aws_access_key_id'],
                aws_secret_access_key=creds['aws_secret_access_key'],
                aws_session_token=creds['session_token'],
            )
