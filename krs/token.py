"""
Get an admin token for KeyCloak.
"""
import logging

import requests
from wipac_dev_tools import from_environment
from rest_tools.client import ClientCredentialsAuth, SavedDeviceGrantAuth


def get_token(url, client_id, client_secret, client_realm='master'):
    url = f'{url}/auth/realms/{client_realm}/protocol/openid-connect/token'
    args = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }
    logging.debug(f'get_token()  url: {url}  client_id: {client_id}')

    r = requests.post(url, data=args)
    r.raise_for_status()
    req = r.json()
    return req['access_token']


def get_rest_client(retries=None, timeout=15):
    config = from_environment({
        'KEYCLOAK_REALM': 'icecube',
        'KEYCLOAK_URL': 'https://keycloak.icecube.wisc.edu',
        'KEYCLOAK_CLIENT_ID': 'rest-access',
        'KEYCLOAK_CLIENT_SECRET': '',
        'KEYCLOAK_CLIENT_REALM': 'master',
    })
    kwargs = {'timeout': timeout}
    if retries is not None:
        kwargs['retries'] = retries
    if config['KEYCLOAK_CLIENT_SECRET']:
        return ClientCredentialsAuth(
            address=f'{config["KEYCLOAK_URL"]}/auth/admin/realms/{config["KEYCLOAK_REALM"]}',
            token_url=f'{config["KEYCLOAK_URL"]}/auth/realms/{config["KEYCLOAK_CLIENT_REALM"]}',
            client_id=config['KEYCLOAK_CLIENT_ID'],
            client_secret=config['KEYCLOAK_CLIENT_SECRET'],
            **kwargs
        )
    else:
        if config['KEYCLOAK_CLIENT_ID'] == 'rest-access':
            config['KEYCLOAK_CLIENT_ID'] = 'rest-access-admin'
        return SavedDeviceGrantAuth(
            address=f'{config["KEYCLOAK_URL"]}/auth/admin/realms/{config["KEYCLOAK_REALM"]}',
            token_url=f'{config["KEYCLOAK_URL"]}/auth/realms/{config["KEYCLOAK_CLIENT_REALM"]}',
            filename='.keycloak-rest-services-auth',
            client_id=config['KEYCLOAK_CLIENT_ID'],
            **kwargs
        )


def main():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='Keycloak tokens')
    subparsers = parser.add_subparsers()
    parser_get = subparsers.add_parser('get', help='get token')
    parser_get.add_argument('url', help='keycloak base url')
    parser_get.add_argument('client_id', help='keycloak client id')
    parser_get.add_argument('client_secret', help='keycloak client secret')
    parser_get.add_argument('--client_realm', default='master', help='keycloak client realm')
    parser_get.set_defaults(func=get_token)
    parser_rc = subparsers.add_parser('rc', help='get rest client')
    parser_rc.set_defaults(func=get_rest_client)
    args = vars(parser.parse_args())

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    func = args.pop('func')
    ret = func(**args)
    if ret is not None:
        pprint(ret)


if __name__ == '__main__':
    main()
