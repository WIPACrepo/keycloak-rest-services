"""IceCube Keycloak setup."""

# fmt: off

import argparse
import asyncio
import os
import sys

# local imports
from krs.bootstrap import bootstrap, get_token, user_mgmt_app
from krs.groups import create_group
from krs.token import get_rest_client

from .institution_list import ICECUBE_INSTS

sys.path.append(os.getcwd())


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
    parser.add_argument('--keycloak_realm', default='IceCube', help='Keycloak realm')
    parser.add_argument('-u', '--username', default='admin', help='admin username')
    parser.add_argument('-p', '--password', default='admin', help='admin password')

    args = parser.parse_args()

    os.environ['KEYCLOAK_REALM'] = args.keycloak_realm
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
            if isinstance(values, dict) and values[name]:
                await create_subgroups(groupname, values[name])
    asyncio.run(create_subgroups('', GROUPS))

    # set up institutions
    async def create_insts(base, inst_list):
        for name in inst_list:
            groupname = base+'/'+name
            await create_group(groupname, attrs=inst_list[name], rest_client=rest_client)
            await create_group(groupname+'/_admin', rest_client=rest_client)
            await create_group(groupname+'/authorlist', rest_client=rest_client)
    asyncio.run(create_insts('/institutions/IceCube', ICECUBE_INSTS))

    # set up user_mgmt app
    token = get_token()
    user_mgmt_app(args.user_mgmt_url, token=token)


if __name__ == '__main__':
    main()
