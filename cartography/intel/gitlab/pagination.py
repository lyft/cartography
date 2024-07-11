from cartography.util import make_requests_url


def paginate_request(url: str, access_token: str):
    items = []
    while url:
        response = make_requests_url(url, access_token, return_raw=True)
        response.raise_for_status()
        items.extend(response.json())

        # Check for pagination
        if "next" in response.links:
            url = response.links["next"]["url"]
        else:
            url = None

    return items
