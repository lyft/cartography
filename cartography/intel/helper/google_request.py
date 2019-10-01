import logging

from googleapiclient.discovery import HttpError
logger = logging.getLogger(__name__)


def repeat_request(req, req_args, req_next, retries=5):
    """ Wrapper to retry requests.  We make a lot of requests to Google.
    Sometimes it may flake out due to network or server issues.  Repeat if it fails.

    :param req: The API request to make
    :param req_args: The API request arguments
    :param req_next: API request for paginatioon
    :param retries: number of retries to attempt
    :return: list of Google API object models
    """
    retry = 0
    request = req(**req_args)
    response_objects = []
    while request is not None:
        try:
            resp = request.execute()
            response_objects.append(resp)
            request = req_next(request, resp)
        except HttpError as e:
            logger.warning(f'HttpError occurred returning empty list. Details: {e}, retry: {retry}')
            retry += 1
            if retry >= retries:
                break
    return response_objects
