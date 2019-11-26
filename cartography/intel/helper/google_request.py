import logging
import time

from googleapiclient.discovery import HttpError
logger = logging.getLogger(__name__)

GOOGLE_API_NUM_RETRIES = 5


class GoogleRetryException(Exception):
    pass


def repeat_request(req, req_args, req_next=None, retries=5, retry_delay_ms=500):
    """ Wrapper to retry requests.  We make a lot of requests to Google.
    Sometimes it may flake out due to network or server 5XX issues.  Repeat if it fails.
    If it's a 4XX

    :param req: The API request to make
    :param req_args: The API request arguments
    :param req_next: API request for pagination
    :param retries: number of retries to attempt
    :param retry_delay_ms: delay in milliseconds before next retry
    :return: list of Google API object models
    """
    retry = 0
    request = req(**req_args)
    response_objects = []

    while request is not None:
        try:
            resp = request.execute(num_retries=GOOGLE_API_NUM_RETRIES)
            response_objects.append(resp)
            request = req_next(request, resp) if req_next else None
            retry = 0
        except HttpError as e:
            if e.resp.status >= 400 and e.resp.status < 500:
                logger.warning(f'HttpError client occurred, skipping.  Details: {e}')
                break
            elif e.resp.status >= 500 and e.resp.status < 600:
                logger.warning(f'HttpError server occurred returning empty list. Details: {e}, retry: {retry}')
                time.sleep(retry_delay_ms / 1000.0)
                if retry >= retries:
                    raise GoogleRetryException(f'Retry limit: {retries} exceeded.')
                retry += 1

    return response_objects
