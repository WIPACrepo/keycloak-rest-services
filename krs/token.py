"""
Get an admin token for KeyCloak.
"""
import logging
from functools import partial

import requests
from rest_tools.server import from_environment
from rest_tools.client import RestClient


def get_token(url, client_id, client_secret, refresh=False):
    url = f'{url}/auth/realms/master/protocol/openid-connect/token'
    args = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    logging.debug(f'get_token()  url: {url}  client_id: {client_id}')

    r = requests.post(url, data=args)
    r.raise_for_status()
    req = r.json()
    if refresh:
        return req['refresh_token']
    else:
        return req['access_token']

def get_rest_client():
    config = from_environment({
        'KEYCLOAK_REALM': None,
        'KEYCLOAK_URL': None,
        'KEYCLOAK_CLIENT_ID': 'rest-access',
        'KEYCLOAK_CLIENT_SECRET': None,
    })
    token_func = partial(get_token, config["KEYCLOAK_URL"],
        client_id=config['KEYCLOAK_CLIENT_ID'],
        client_secret=config['KEYCLOAK_CLIENT_SECRET'],
    )
    return RestClient(
        f'{config["KEYCLOAK_URL"]}/auth/admin/realms/{config["KEYCLOAK_REALM"]}',
        token=token_func,
        timeout=10,
    )
