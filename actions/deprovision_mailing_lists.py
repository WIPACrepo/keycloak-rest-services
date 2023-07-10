"""
See docstring of deprovision_mailing_lists()

Remove from KeyCloak mailing list groups (the subgroups of the given mailing
list group tree root) users who are not members those groups' respective
`allow_members_from_group_trees` attributes. Users that have the attribute
`institutionless_since` set will be given the provided grace period before
removal.

The grace period is intended to avoid removal of users who are changing
institutions (i.e. when a user is removed from institution A before being
added to institution B). Note that users who are part of multiple institutions
will be removed immediately, since they will not have `institutionless_since`
set after being removed from only one institution.

Similarly, it is important that whatever updates `institutionless_since` is
run before this action. Otherwise when a user is removed from their last
institution, they will no longer satisfy the `allow_members_from_group_trees`
constraint, but their `institutionless_since` won't be set. (This is a race
condition, so the grace period mechanism isn't 100% reliable.)

Example::

       python -m actions.deprovision_mailing_lists --ml-group-root /test-mail
"""
import asyncio
import logging

from datetime import datetime, timedelta

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, remove_user_group
from krs.users import user_info


logger = logging.getLogger('deprovision_mailing_lists')


async def get_group_tree_membership(root_group_path, ignore_subgroup_names, keycloak_client):
    """Recursively get all usernames of a group tree, ignoring subgroups with the given names."""
    usernames = await get_group_membership(root_group_path, rest_client=keycloak_client)
    root_group = await group_info(root_group_path, rest_client=keycloak_client)
    subgroup_paths = [sg['path'] for sg in root_group['subGroups'] if sg['name'] not in ignore_subgroup_names]
    for subgroup_path in subgroup_paths:
        usernames.extend(await get_group_tree_membership(subgroup_path, ignore_subgroup_names, keycloak_client))
    return list(set(usernames))


async def deprovision_mailing_lists(mailing_list_group_root, removal_grace_days, keycloak_client, dryrun=False):
    """Remove from all mailing list groups under the given root the users who
    are not members of groups listed in the `allow_members_from_group_trees`
    attributes of those groups. Users with the `institutionless_since`
    attribute will be given the provided grace period before removal.

    The grace period is intended to avoid removal of users who are changing
    institutions (i.e. when a user is removed from institution A before being
    added to institution B). Note that users who are part of multiple institutions
    will be removed immediately, since they will not have `institutionless_since`
    set after being removed from only one institution.

    Args:
        mailing_list_group_root (str): KeyCloak path to mailing list group tree
        removal_grace_days (int): delay of removal of institutionless users
        keycloak_client (RestClient): KeyCloak REST API client
        dryrun (bool): perform a mock run with no changes made
    """
    ml_root_group = await group_info(mailing_list_group_root, rest_client=keycloak_client)

    for ml_group in ml_root_group['subGroups']:
        allowed_group_trees = ml_group['attributes']['allow_members_from_group_trees']
        if not isinstance(allowed_group_trees, list):
            allowed_group_trees = [allowed_group_trees]
        allowed_users = set()
        for allowed_group_tree in allowed_group_trees:
            allowed_users.update(await get_group_tree_membership(allowed_group_tree, ['_admin'], keycloak_client))

        ml_group_members = set(await get_group_membership(ml_group['path'], rest_client=keycloak_client))
        for username in ml_group_members - allowed_users:
            logger.debug(f'{username} is not allowed to be in {ml_group["path"]}')
            user = await user_info(username, rest_client=keycloak_client)
            if 'institutionless_since' in user['attributes']:
                institutionless_since = datetime.fromisoformat(user['attributes']['institutionless_since'])
                institutionless_for = datetime.now() - institutionless_since
                if institutionless_for < timedelta(days=removal_grace_days):
                    logger.debug(f'Leaving {username} alone because grace period hasn\'t expired')
                    continue
            logger.info(f'Removing {username} from {ml_group["path"]} (dryrun={dryrun})')
            if not dryrun:
                await remove_user_group(ml_group['path'], username, rest_client=keycloak_client)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove from KeyCloak mailing list groups users who are not part of '
                    'those groups\' experiment.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--ml-group-root', metavar='GROUP_PATH', required=True,
                        help='root of the mailing list group tree')
    parser.add_argument('--removal-grace', metavar='DAYS', default=3, type=int,
                        help='how much to delay removal of institutionless users')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(deprovision_mailing_lists(args['ml_group_root'], args['removal_grace'], keycloak_client, args['dryrun']))


if __name__ == '__main__':
    main()
