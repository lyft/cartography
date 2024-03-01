"""Error handler class"""
# define Python user-defined exceptions


class ServerError(Exception):
    """Base Class for all other application exceptions"""


class InvalidTemplateTypeError(ServerError):
    """Raised when Template Type is Invalid"""


class AWSPermissionError(ServerError):
    """Raised when AWS throws Permission error"""


class AWSRequestError(ServerError):
    """Raised when any of the AWS Request fails"""


class InvalidRuleError(ServerError):
    """Raised when Rule is invalid"""


class GraphRequestError(ServerError):
    """Raised when Graph Requests fail"""


class PubSubPublishError(ServerError):
    """ Raised when publishing message to Google PubSub fails"""


class TimeLimitError(ServerError):
    """Raised when Processing Time reaches limit"""


def classify_error(logger, err, msg, extra=None):
    """Classify the error to Permission or Request Processing Error"""
    message = f'{msg}: {err}'
    if err.response['Error']['Code'] == 'AccessDenied' or \
            err.response['Error']['Code'] == 'AccessDeniedException' or \
            err.response['Error']['Code'] == 'UnauthorizedOperation' or \
            err.response['Error']['Code'] == 'Client.UnauthorizedOperation':
        logger.exception(f'Insufficient permissions. {message}', extra=extra)
        return AWSPermissionError(message)

    else:
        logger.exception(message, extra=extra)
        return AWSRequestError(message)
