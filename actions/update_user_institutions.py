"""
Update user attributes that allow detection of changes of users' institutions:
* institutions_last_seen: coma-separated list of the user's institutions (group
                          paths) as of the last time this action ran.
* institutions_last_changed: time in ISO 8601 format when institutions_last_seen
                             of the user was last updated.

Note that the reason institutions_last_seen is a comma-separated list is that
currently our KeyCloak instance can't store lists as user attribute values.

Example::
    python -m actions.update_user_institutions --dryrun
"""
import asyncio
import logging
from datetime import datetime
from collections import defaultdict

from krs.token import get_rest_client
from krs.groups import get_group_membership
from krs.institutions import list_insts
from krs.users import list_users, modify_user

logger = logging.getLogger('update_user_institutions')


async def update_institution_tracking(keycloak_client=None, dryrun=False):
    """Update institutions_last_seen and institutions_last_changed user attributes.

    Args
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """

    user_insts = defaultdict(list)
    insts = await list_insts(rest_client=keycloak_client)
    for inst_path in insts.keys():
        inst_usernames = await get_group_membership(inst_path, rest_client=keycloak_client)
        for inst_username in inst_usernames:
            user_insts[inst_username].append(inst_path)

    all_users = await list_users(rest_client=keycloak_client)
    for username,userinfo in all_users.items():
        insts_actual = user_insts[username]
        # There's currently an issue with our keycloak that prevents using lists
        # as user attribute values. To work-around, institutions_last_seen is
        # stored as comma-separated string.
        insts_last_seen = userinfo["attributes"].get("institutions_last_seen", '')
        insts_last_seen = [i.strip() for i in insts_last_seen.split(',') if i.strip()]
        if set(insts_actual) != set(insts_last_seen):
            logger.info(f"{username}'s institutions have changed from "
                        f"{insts_last_seen} to {insts_actual}")
            attribs = {"institutions_last_seen": ','.join(insts_actual),
                       "institutions_last_changed": datetime.now().isoformat()}
            if not dryrun:
                await modify_user(username, attribs=attribs, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Update institutions_last_seen and institutions_last_changed user '
                    'attributes. See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(update_institution_tracking(keycloak_client, args['dryrun']))


if __name__ == '__main__':
    main()
