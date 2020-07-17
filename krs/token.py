"""
Get an admin token for KeyCloak.
"""
import logging
import time

import requests
import jwt

from .util import config, ConfigRequired


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
