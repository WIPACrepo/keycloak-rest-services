"""
Get an admin token for KeyCloak.
"""
import requests

from .util import config, ConfigRequired


def get_token(from_cache=True):
    if from_cache and get_token.cache:
        return get_token.cache

    cfg = config({
        'keycloak_url': ConfigRequired,
        'client_id': ConfigRequired,
        'client_secret': ConfigRequired,
    })
    url = f'{cfg["keycloak_url"]}/auth/realms/master/protocol/openid-connect/token'
    args = {
        'client_secret': cfg['client_secret'],
        'client_id': cfg['client_id'],
        'grant_type': 'client_credentials',
    }

    r = requests.post(url, data=args)
    r.raise_for_status()
    req = r.json()
    get_token.cache = req['access_token']
    return get_token.cache
get_token.cache = None
