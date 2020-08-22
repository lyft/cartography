import logging

import botocore

logger = logging.getLogger(__name__)


def aws_handle_regions(func):
    ERROR_CODES = [
        'AccessDeniedException',
        'UnrecognizedClientException',
        'InvalidClientTokenId',
        'AuthFailure',
    ]

    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as e:
            # The account is not authorized to use this service in this region
            # so we can continue without raising an exception
            if e.response['Error']['Code'] in ERROR_CODES:
                logger.warning("{} in this region. Skipping...".format(e.response['Error']['Message']))
                return []
            else:
                raise
    return inner_function
