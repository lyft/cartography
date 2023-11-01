# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html
# https://github.com/awsdocs/aws-doc-sdk-examples/tree/master/python/example_code/sns
# https://docs.aws.amazon.com/sns/latest/api/CommonErrors.html
import os

from boto3.session import Session
from botocore.exceptions import ClientError

from utils.errors import classify_error


class SNSLibrary:
    def __init__(self, context):
        self.context = context

        # Create a Session with the credentials passed
        session = Session()

        # if it's an offline test, use offline SNS
        if os.getenv('IS_OFFLINE'):
            try:
                self.sns_client = session.client(
                    'sns', region_name=self.context.region, endpoint_url=self.context.sns_offline_url,
                )

            except ClientError as e:
                raise classify_error(self.context.logger, e, 'Failed to create SNS client')

        else:
            self.sns_client = session.client('sns', region_name=self.context.region)

    def publish(self, message, topic):
        try:
            if self.context.app_env == 'PRODUCTION':
                self.sns_client.publish(
                    Message=message,
                    TopicArn=topic,
                )

                return True

            else:
                self.context.logger.info('SNS Publish -> Non-Production environment')
                return True

        except ClientError as e:
            raise classify_error(self.context.logger, e, 'Failed to publish message', {'topic': topic})
