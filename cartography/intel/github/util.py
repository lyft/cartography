import json
import logging
import time
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import requests

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


def call_github_api(query: str, variables: str, token: str, api_url: str) -> Dict:
    """
    Calls the GitHub v4 API and executes a query
    :param query: the GraphQL query to run
    :param variables: parameters for the query
    :param token: the Oauth token for the API
    :param api_url: the URL to call for the API
    :return: query results json
    """
    headers = {'Authorization': f"token {token}"}
    try:
        response = requests.post(
            api_url,
            json={'query': query, 'variables': variables},
            headers=headers,
            timeout=_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        # Add context and re-raise for callers to handle
        logger.warning("GitHub: requests.get('%s') timed out.", api_url)
        raise
    response.raise_for_status()
    return response.json()


def fetch_page(token: str, api_url: str, organization: str, query: str, cursor: Optional[str] = None) -> Dict:
    """
    Return a single page of max size 100 elements from the Github api_url using the given `query` and `cursor` params.
    :param token: The API token as string. Must have permission for the object being paginated.
    :param api_url: The Github API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param query: The GraphQL query, e.g. `GITHUB_ORG_USERS_PAGINATED_GRAPHQL`
    :param cursor: The GraphQL cursor string (behaves like a page number) for Github objects in the given
    organization. If None, the Github API will return the first page of repos.
    :return: The raw response object from the requests.get().json() call.
    """
    gql_vars = {
        'login': organization,
        'cursor': cursor,
    }
    gql_vars_json = json.dumps(gql_vars)
    response = call_github_api(query, gql_vars_json, token, api_url)
    return response


def fetch_all(
    token: str, api_url: str, organization: str, query: str, resource_type: str, field_name: str, retries: int = 5,
) -> Tuple[List[Dict], Dict]:
    """
    Fetch and return all data items of the given `resource_type` and `field_name` from Github's paginated GraphQL API as
    a list, along with information on the organization that they belong to.
    :param token: The Github API token as string.
    :param api_url: The Github v4 API endpoint as string.
    :param organization: The name of the target Github organization as string.
    :param query: The GraphQL query, e.g. `GITHUB_ORG_USERS_PAGINATED_GRAPHQL`
    :param resource_type: The name of the paginated resource under the organization e.g. `membersWithRole` or
    `repositories`. See the fields under https://docs.github.com/en/graphql/reference/objects#organization for a full
    list.
    :param field_name: The field name of the resource_type to append items from - this is usually "nodes" or "edges".
    See the field list in https://docs.github.com/en/graphql/reference/objects#repositoryconnection for other examples.
    :param retries: Number of retries to perform.  Github APIs are often flakey and retrying the request helps.
    :return: A 2-tuple containing 1. A list of data items of the given `resource_type` and `field_name`,  and 2. a dict
    containing the `url` and the `login` fields of the organization that the items belong to.
    """
    cursor = None
    has_next_page = True
    data: List[Dict] = []
    retry = 0
    while has_next_page:
        try:
            resp = fetch_page(token, api_url, organization, query, cursor)
        except requests.exceptions.Timeout:
            retry += 1
            if retry >= retries:
                logger.error(
                    f"GitHub: Could not retrieve page of resource {resource_type} due to API timeout.",
                    exc_info=True,
                )
                raise
            else:
                time.sleep(1 * retry)
                continue
        except requests.exceptions.HTTPError:
            retry += 1
            if retry >= retries:
                logger.error(
                    f"GitHub: Could not retrieve page of resource `{resource_type}` due to HTTP error.",
                    exc_info=True,
                )
                raise
            else:
                time.sleep(1 * retry)
                continue
        resource = resp['data']['organization'][resource_type]
        data.extend(resource[field_name])
        cursor = resource['pageInfo']['endCursor']
        has_next_page = resource['pageInfo']['hasNextPage']
    org_data = {'url': resp['data']['organization']['url'], 'login': resp['data']['organization']['login']}
    return data, org_data
