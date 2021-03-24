"""
Creates a POSIX user account in LDAP for anyone in the specified Keycloak group.
"""
import logging
import asyncio

from krs.groups import get_group_membership
from krs.users import modify_user
from krs.token import get_rest_client
from krs.ldap import LDAP

async def process(group_path, keycloak_client=None, ldap_client=None):
    # get highest uid, gid in ldap
    max_uid = 0
    max_gid = 0
    users = ldap_client.list_users(['uidNumber', 'gidNumber'])
    for username in users:
        user = users[username]
        if 'uidNumber' in user and user['uidNumber'] > max_uid:
            max_uid = user['uidNumber']
        if 'gidNumber' in user and user['gidNumber'] > max_gid:
            max_gid = user['gidNumber']
    max_id = max(max_uid, max_gid)

    ret = await get_group_membership(group_path, rest_client=keycloak_client)
    for username in ret:
        if username in users and 'uidNumber' in users[username]:
            continue
        # modify user account in LDAP
        max_id += 1
        attribs = {'uidNumber': max_id, 'gidNumber': max_id, 'homeDirectory': f'/home/{username}'}
        ldap_client.modify_user(username, attribs, objectClass='posixAccount')

        # add attrs to Keycloak
        await modify_user(username, attribs, rest_client=keycloak_client)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Create POSIX accounts')
    parser.add_argument('group_path', default='/posix', help='group path (/parentA/parentB/name)')
    parser.add_argument('--log_level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    ldap_client = LDAP()

    asyncio.run(process(args['group_path'], keycloak_client=keycloak_client, ldap_client=ldap_client))


if __name__ == '__main__':
    main()
