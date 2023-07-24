"""
Remove from KeyCloak mailing list groups (subgroups of /mail) users who are
not members of the experiments listed in their `allow_members_from_experiments`
attributes. Users that have recently changed institutions will be granted the
specified grace period before removal.

The grace period is intended to avoid removal of users who are in the midst
of changing institutions (i.e. when a user is already removed from institution
A but before their request to be added to institution B has been approved).

This code relies on the `institutions_last_seen` and `institutions_last_changed`
user attributes, and, consequently, on the Keycloak Rest Services action that
updates those attributes.

Example::
       python -m actions.deprovision_mailing_lists --dryrun
"""
import asyncio
import logging

from datetime import datetime, timedelta

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, remove_user_group
from krs.users import user_info
from krs.institutions import list_insts

logger = logging.getLogger('deprovision_mailing_lists')


async def deprovision_mailing_lists(removal_grace_days, keycloak_client, dryrun=False):
    """Remove from all mailing list groups (subgroups of /mail) the users who
    are not members of experiments listed in the `allow_members_from_experiments`
    attributes of those groups. Users that have recently changed institutions
    will be granted the given grace period before removal.

    Args:
        removal_grace_days (int): delay of removal of institutionless users
        keycloak_client (RestClient): KeyCloak REST API client
        dryrun (bool): perform a mock run with no changes made
    """
    user_info_cache = {}
    ml_root_group = await group_info('/mail', rest_client=keycloak_client)
    for ml_group in ml_root_group['subGroups']:
        allowed_experiments = ml_group['attributes'].get('allow_members_from_experiments')
        if not allowed_experiments:
            logger.warning(f"Skipping {ml_group['path']} because allow_members_from_experiments attribute is missing or empty")
            continue
        if not isinstance(allowed_experiments, list):
            allowed_experiments = [allowed_experiments]

        allowed_institutions = set()
        for experiment in allowed_experiments:
            insts = await list_insts(experiment, rest_client=keycloak_client)
            allowed_institutions.update(insts.keys())

        ml_group_members = await get_group_membership(ml_group['path'], rest_client=keycloak_client)
        for username in ml_group_members:
            try:
                user = user_info_cache[username]
            except KeyError:
                user = await user_info(username, rest_client=keycloak_client)
                user_info_cache[username] = user

            user_insts = user['attributes'].get('institutions_last_seen', '')
            user_insts = [i.strip() for i in user_insts.split(',') if i.strip()]
            if not allowed_institutions.intersection(user_insts):
                logger.info(f'User {username} is not allowed to be in {ml_group["path"]}')
                if 'institutions_last_changed' in user['attributes']:
                    insts_changed = user['attributes']['institutions_last_changed']
                    insts_changed = datetime.fromisoformat(insts_changed)
                    time_since_inst_change = datetime.now() - insts_changed
                    if time_since_inst_change < timedelta(days=removal_grace_days):
                        logger.info(f'Leaving {username} alone because grace period hasn\'t expired')
                        continue
                logger.info(f'Removing {username} from {ml_group["path"]} (dryrun={dryrun})')
                if not dryrun:
                    await remove_user_group(ml_group['path'], username, rest_client=keycloak_client)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove from KeyCloak mailing list groups users who are not part of '
                    'those lists\' allowed institutions/experiments/projects. See file '
                    'docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--removal-grace', metavar='DAYS', default=3, type=int,
                        help='how much to delay removal of institutionless users')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'),
                        help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(deprovision_mailing_lists(args['removal_grace'], keycloak_client, args['dryrun']))


if __name__ == '__main__':
    main()
