import argparse
import asyncio
import logging

from krs.ldap import LDAP, get_ldap_members
from krs.groups import create_group, add_user_group
from krs.bootstrap import get_token
from krs.token import get_rest_client

logger = logging.getLogger('import_ldap')


IGNORE_LIST = set(['IceCube', 'wipac'])

async def import_ldap_groups(keycloak_conn, ldap_setup=True, dryrun=False):
    ldap_conn = LDAP()

    if ldap_setup:
        # start with LDAP setup
        ldap_conn.keycloak_ldap_link(get_token())
        ldap_conn.force_keycloak_sync()

    ldap_users = ldap_conn.list_users()
    ldap_groups = ldap_conn.list_groups()

    for group_name in sorted(ldap_groups):
        members = get_ldap_members(ldap_groups[group_name])
        gidNumber = ldap_groups[group_name]['gidNumber']

        if group_name in IGNORE_LIST:
            logger.info(f'skipping ignored group {group_name}')
        elif not members:
            logger.info(f'skipping empty group {group_name}')
        elif group_name in ldap_users:
            # this is a user group
            if members == [group_name]:
                logger.info(f'skipping 1:1 user group {group_name}')
            else:
                logger.info(f'creating user group /posix/{group_name} with members {members}')
                if not dryrun:
                    await create_group(f'/posix/{group_name}', {'gidNumber': gidNumber}, rest_client=keycloak_conn)
                    for member in members:
                        await add_user_group(f'/posix/{group_name}', member, rest_client=keycloak_conn)
        else:
            logger.info(f'creating non-user group /posix/{group_name} with members {members}')
            if not dryrun:
                await create_group(f'/posix/{group_name}', {'gidNumber': gidNumber}, rest_client=keycloak_conn)
                for member in members:
                    await add_user_group(f'/posix/{group_name}', member, rest_client=keycloak_conn)


def main():
    parser = argparse.ArgumentParser(description='IceCube Keycloak setup')
    parser.add_argument('--dryrun', action='store_true', help='dry run')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    rest_client = get_rest_client()
    asyncio.run(import_ldap_groups(rest_client, ldap_setup=False, dryrun=args.dryrun))


if __name__ == '__main__':
    main()
