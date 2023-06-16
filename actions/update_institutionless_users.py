"""
Manage the institutionless_since attribute of keycloak users:
- If a user does not belong to any institution group and does not already have the
    institutionless_since attribute, create and set it to current time.
- If a user belongs to an institution group and has the institutionless_since
    attribute defined, delete this attribute.

Example::
    python -m actions.update_institutionless_users
"""
import asyncio
import logging
from datetime import datetime

from krs.token import get_rest_client
from krs.groups import get_group_membership
from krs.institutions import list_insts
from krs.users import list_users, modify_user

logger = logging.getLogger('update_institutionless_users')


async def update_institutionless_users(keycloak_client, dryrun=False):
    """Manage the institutionless_since attribute based on users' institution membership.

    Users that belong to an institution group should not have institutionless_since
      attribute. Users that don't belong to any institution should have
      institutionless_since set to the time when it was first detected that they
      are institutionless. The timestamp should be a string in ISO 8601 format.

    Args
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    all_users = await list_users(rest_client=keycloak_client)

    institutions = await list_insts(rest_client=keycloak_client)
    institutioned_usernames = set()  # i.e. users that belong to an institution
    for inst_path in institutions.keys():
        inst_usernames = await get_group_membership(inst_path, rest_client=keycloak_client)
        institutioned_usernames.update(inst_usernames)

    for username in institutioned_usernames:
        if 'institutionless_since' in all_users[username]['attributes']:
            logger.info(f'Removing "institutionless_since" attribute from {username} (dryrun={dryrun})')
            if not dryrun:
                await modify_user(username, attribs={'institutionless_since': None}, rest_client=keycloak_client)

    now = datetime.now().isoformat()
    institutionless_usernames = set(all_users) - institutioned_usernames
    for username in institutionless_usernames:
        if 'institutionless_since' not in all_users[username]['attributes']:
            logger.info(f'Setting "institutionless_since" attribute of {username} (dryrun={dryrun})')
            if not dryrun:
                await modify_user(username, attribs={'institutionless_since': now}, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Manage the "institutionless_since" user attribute. '
                    'See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(update_institutionless_users(keycloak_client, args['dryrun']))


if __name__ == '__main__':
    main()
