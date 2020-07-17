import os
import sys
import argparse
import asyncio

import requests

sys.path.append(os.getcwd())

from krs.bootstrap import bootstrap, user_mgmt_app
from krs.groups import create_group
from krs.token import get_token
from krs.util import config, ConfigRequired


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

    os.environ['realm'] = 'IceCube'
    os.environ['keycloak_url'] = args.keycloak_url
    os.environ['username'] = args.username
    os.environ['password'] = args.password

    # set up realm and REST API
    secret = bootstrap()
    os.environ['client_id'] = 'rest-access'
    os.environ['client_secret'] = secret
    token = get_token()

    # set up basic group structure
    async def create_subgroups(root, values):
        for name in values:
            groupname = root+'/'+name
            await create_group(groupname, token=token)
            if values[name]:
                await create_subgroups(groupname, values[name])
    asyncio.run(create_subgroups('', GROUPS))

    # set up user_mgmt app
    user_mgmt_app(args.user_mgmt_url, token=token)


if __name__ == '__main__':
    main()
