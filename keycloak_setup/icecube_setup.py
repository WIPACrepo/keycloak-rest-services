"""
IceCube Keycloak setup.

Example command:

    python -m keycloak_setup.icecube_setup --ldap_url ldaps://XXXX --ldap_admin_user 'uid=admin,XXXX' --ldap_admin_password XXXX --keycloak_realm IceCube -u XXXX -p XXXX https://keycloak.XXXX https://user-mgmt.XXXX
"""

# fmt: off

import argparse
import asyncio
import logging
import os
import sys

# local imports
from krs.bootstrap import bootstrap, get_token, user_mgmt_app
from krs.groups import create_group
from krs.institutions import create_inst
from krs.token import get_rest_client

from .institution_list import ICECUBE_INSTS, GEN2_INSTS
from .icecube_ldap import import_ldap_groups, import_ldap_insts

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
    parser.add_argument('--ldap_url', default=None, help='LDAP url')
    parser.add_argument('--ldap_setup', default=False, action='store_true', help='setup LDAP')
    parser.add_argument('--ldap_admin_user', default='admin', help='LDAP admin username')
    parser.add_argument('--ldap_admin_password', default='admin', help='LDAP admin password')
    parser.add_argument('--keycloak_realm', default='IceCube', help='Keycloak realm')
    parser.add_argument('-u', '--username', default='admin', help='Keycloak admin username')
    parser.add_argument('-p', '--password', default='admin', help='Keycloak admin password')

    args = parser.parse_args()

    os.environ['KEYCLOAK_REALM'] = args.keycloak_realm
    os.environ['KEYCLOAK_URL'] = args.keycloak_url
    if args.ldap_url:
        os.environ['LDAP_URL'] = args.ldap_url
        os.environ['LDAP_ADMIN_USER'] = args.ldap_admin_user
        os.environ['LDAP_ADMIN_PASSWORD'] = args.ldap_admin_password
    os.environ['USERNAME'] = args.username
    os.environ['PASSWORD'] = args.password

    logging.basicConfig(level=logging.DEBUG)

    # set up realm and REST API
    secret = bootstrap()
    os.environ['KEYCLOAK_CLIENT_ID'] = 'rest-access'
    os.environ['KEYCLOAK_CLIENT_SECRET'] = secret
    rest_client = get_rest_client(retries=1, timeout=30)

    # set up basic group structure
    async def create_subgroups(root, values):
        for name in values:
            groupname = root+'/'+name
            await create_group(groupname, rest_client=rest_client)
            if isinstance(values, dict) and values[name]:
                await create_subgroups(groupname, values[name])
    asyncio.run(create_subgroups('', GROUPS))

    # set up institutions
    async def create_insts(exp, inst_list):
        for name in inst_list:
            attrs = {k: inst_list[name][k] for k in inst_list[name] if not k.startswith('_')}
            await create_inst(exp, name, attrs, rest_client)
    asyncio.run(create_insts('IceCube', ICECUBE_INSTS))
    asyncio.run(create_insts('IceCube-Gen2', ICECUBE_INSTS))
    asyncio.run(create_insts('IceCube-Gen2', GEN2_INSTS))

    if args.ldap_url:
        # sync ldap groups
        asyncio.run(import_ldap_groups(rest_client, ldap_setup=args.ldap_setup))
        asyncio.run(import_ldap_insts(rest_client))
        asyncio.run(import_ldap_insts(rest_client, base_group='/institutions/IceCube-Gen2', INSTS=ICECUBE_INSTS))
        asyncio.run(import_ldap_insts(rest_client, base_group='/institutions/IceCube-Gen2', INSTS=GEN2_INSTS))

    # set up user_mgmt app
    token = get_token()
    user_mgmt_app(args.user_mgmt_url, token=token)


if __name__ == '__main__':
    main()
