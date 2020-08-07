import os
import sys
import argparse
import asyncio

import requests

sys.path.append(os.getcwd())

from krs.bootstrap import bootstrap, user_mgmt_app, get_token
from krs.groups import create_group
from krs.token import get_rest_client


GROUPS = {
    'institutions': {
        'IceCube': {},
        'IceCube-Gen2': {},
        'HAWC': {},
        'CTA': {},
        'ARA': {},
    },
    'experiments': {
        'IceCube': {
            'Working Groups': {},
        },
    },
    'posix': {},
    'tokens': {},
}


def main():
    parser = argparse.ArgumentParser(description='IceCube Keycloak setup')
    parser.add_argument('keycloak_url', help='Keycloak url')
    parser.add_argument('user_mgmt_url', help='User Management url')
    parser.add_argument('-u','--username', default='admin', help='admin username')
    parser.add_argument('-p','--password', default='admin', help='admin password')

    args = parser.parse_args()

    os.environ['KEYCLOAK_REALM'] = 'IceCube'
    os.environ['KEYCLOAK_URL'] = args.keycloak_url
    os.environ['USERNAME'] = args.username
    os.environ['PASSWORD'] = args.password

    # set up realm and REST API
    secret = bootstrap()
    os.environ['KEYCLOAK_CLIENT_ID'] = 'rest-access'
    os.environ['KEYCLOAK_CLIENT_SECRET'] = secret
    rest_client = get_rest_client()

    # set up basic group structure
    async def create_subgroups(root, values):
        for name in values:
            groupname = root+'/'+name
            await create_group(groupname, rest_client=rest_client)
            if values[name]:
                await create_subgroups(groupname, values[name])
    asyncio.run(create_subgroups('', GROUPS))

    # set up user_mgmt app
    token = get_token()
    user_mgmt_app(args.user_mgmt_url, token=token)


if __name__ == '__main__':
    main()
