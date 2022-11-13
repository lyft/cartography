from falconpy.oauth2 import OAuth2


def get_authorization(client_id: str, client_secret: str, api_url: str) -> OAuth2:
    authorization = OAuth2(
        creds={"client_id": client_id, "client_secret": client_secret},
        base_url=api_url,
    )
    return authorization
