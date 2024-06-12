"""
Recursively remove from either the given group, or every mailing list group
(i.e. direct subgroups of /mail) users who are not active members of the
institutions belonging to the experiments listed in the top-level group's
`allow_members_from_experiments` attribute. A user's institutions are
determined based on their `institutions_last_seen` attribute (and not the
actual institution membership at the time of execution).

`Allow_members_from_experiments` must be a list whose elements are experiment
names matching the names of subgroups of /institutions, such as IceCube, IceCube-Gen2.

Recursive subgroups of a mailing group are not allowed to define their own
`allow_members_from_experiments`.

Nothing is done if the top-level group doesn't have `allow_members_from_experiments`.

Users who have recently changed institutions will be granted the specified grace
period in order to avoid removal of users who are in the midst of institution switch
(i.e. when a user is already removed from institution A but before their request
to be added to institution B has been approved).

This code relies on the `institutions_last_seen` and `institutions_last_changed`
user attributes, and, consequently, on the Keycloak Rest Services action that
updates those attributes (track_user_institutions.py at the time of writing).
Users that don't have `institutions_last_seen` defined are assumed to belong
to no institution.

Users can optionally be notified of changes via email. SMTP server is
controlled by the EMAIL_SMTP_SERVER environmental variable and defaults
to localhost. See krs/email.py for more email options.

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes
PLEASE KEEP THAT PAGE UPDATED IF YOU MAKE CHANGES RELATED TO CUSTOM
KEYCLOAK ATTRIBUTES USED IN THIS CODE.

Example::
       python -m actions.prune_mail_groups_by_experiment --dryrun
"""
import asyncio
import logging

from datetime import datetime, timedelta

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, remove_user_group
from krs.users import user_info
from krs.institutions import list_insts
from krs.email import send_email

from actions.util import group_tree_to_list

logger = logging.getLogger('prune_mail_groups_by_experiment')

REMOVAL_MESSAGE = """
You have been removed from group {group_path} because you do not meet
the requirement of being a member of an institution belonging to
{experiments} experiment(s).

This message was generated by the prune_mail_groups_by_experiment robot.
Please contact help@icecube.wisc.edu for support.
"""


async def _prune_group(group_path, removal_grace_days, allowed_institutions,
                       user_info_cache, keycloak_client, dryrun=False):
    """Remove from group_path users who are not members of allowed_institutions.

    Users that have recently changed institutions will be granted the given grace
    period before removal. Relies on user attributes `institutions_last_seen` and
    `institutions_last_changed`.

    Args:
        group_path (str): path of the group to be worked on
        removal_grace_days (int): delay of user removal
        allowed_institutions (set): set of full group paths of allowed institutions
        user_info_cache (dict): cache for user_info objects
        keycloak_client (RestClient): KeyCloak REST API client
        dryrun (bool): perform a mock run with no changes made
    Returns:
        list of usernames that were removed
    """
    removed_users = []
    ml_group_members = await get_group_membership(group_path, rest_client=keycloak_client)
    for username in ml_group_members:
        try:
            user = user_info_cache[username]
        except KeyError:
            user = await user_info(username, rest_client=keycloak_client)
            user_info_cache[username] = user

        user_insts = user['attributes'].get('institutions_last_seen', '')
        user_insts = [i.strip() for i in user_insts.split(',') if i.strip()]
        if not allowed_institutions.intersection(user_insts):
            logger.info(f'User {username} is not allowed to be in {group_path}')
            if 'institutions_last_changed' in user['attributes']:
                insts_changed = user['attributes']['institutions_last_changed']
                insts_changed = datetime.fromisoformat(insts_changed)
                time_since_inst_change = datetime.now() - insts_changed
                if time_since_inst_change < timedelta(days=removal_grace_days):
                    logger.info(f"Leaving {username} alone because grace period hasn't expired")
                    continue
            logger.info(f'Removing {username} from {group_path} (dryrun={dryrun})')
            removed_users.append(username)
            if not dryrun:
                await remove_user_group(group_path, username, rest_client=keycloak_client)
    return removed_users


async def prune_mail_groups(removal_grace_days, single_group,
                            send_notifications, keycloak_client, dryrun=False):
    """Recursively remove from mail group(s) users who are not members of the
    experiments listed in the `allow_members_from_experiments` attribute.

    Recursively remove from the given mailing group, or all mailing groups (direct
    subgroups of /mail), and their _admin subgroups, the users who are not members
    of the experiments listed in the `allow_members_from_experiments` attributes
    of those groups. Users that have recently changed institutions will be granted
    the given grace period before removal. Optionally, notify users. Relies on user
    attributes `institutions_last_seen` and `institutions_last_changed`.

    Args:
        removal_grace_days (int): delay of user removal
        single_group (str|None): only consider this group instead of all groups
        send_notifications (bool): whether to send email notifications
        keycloak_client (RestClient): KeyCloak REST API client
        dryrun (bool): perform a mock run with no changes made
    """
    user_info_cache = {}
    ml_root_group = await group_info('/mail', rest_client=keycloak_client)

    if single_group:
        logger.warning(f"Only group {single_group} will be considered.")
        ml_groups = [sg for sg in ml_root_group['subGroups'] if sg['name'] == single_group]
    else:
        ml_groups = ml_root_group['subGroups']

    for ml_group in ml_groups:
        # Build a list of allowed institutions
        allowed_experiments = ml_group['attributes'].get('allow_members_from_experiments')
        if not allowed_experiments:
            logger.info(f"Skipping {ml_group['path']} because allow_members_from_experiments is missing or empty")
            continue
        allowed_experiments_list = (allowed_experiments if isinstance(allowed_experiments, list)
                                    else [allowed_experiments])
        allowed_institutions = set()
        for experiment in allowed_experiments_list:
            insts = await list_insts(experiment, rest_client=keycloak_client)
            allowed_institutions.update(insts.keys())

        groups_for_pruning = group_tree_to_list(ml_group)

        # Guard against subgroups defining their own allow_members_from_experiments
        if any('allow_members_from_experiments' in subgroup['attributes']
               for subgroup in groups_for_pruning[1:]):
            logger.error(f"A subgroup of {ml_group['path']} has an allow_members_from_experiments "
                         f"attribute. This is not allowed. Skipping group pruning.")
            continue

        for group in groups_for_pruning:
            logger.info(f"Pruning group {group['path']}")
            if removed_users := await _prune_group(group['path'], removal_grace_days,
                                                   allowed_institutions, user_info_cache,
                                                   keycloak_client, dryrun):
                logger.info(f"Removed users: {removed_users} ({dryrun=} {send_notifications=})")
                if not dryrun and send_notifications:
                    for username in removed_users:
                        logger.info(f"Notifying {username} of removal from {group['path']}")
                        send_email(username + '@icecube.wisc.edu',
                                   f"You have been removed from {group['path']}",
                                   REMOVAL_MESSAGE.format(
                                       group_path=group['path'],
                                       experiments=' '.join(allowed_experiments_list)),
                                   headline="IceCube Mailing List Management")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Recursively remove from KeyCloak mailing list groups users who are '
                    'not part of those lists\' allowed institutions/experiments/projects. '
                    'See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--removal-grace', metavar='DAYS', default=7, type=int,
                        help='how much to delay removal of institutionless users')
    parser.add_argument('--send-notifications', action='store_true',
                        help='send email notifications to users')
    parser.add_argument('--single-group', metavar='NAME',
                        help='only consider group /mail/NAME')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'),
                        help='logging level')
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run: make no changes and send no notifications')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(prune_mail_groups(
        args['removal_grace'],
        args['single_group'],
        args['send_notifications'],
        keycloak_client,
        args['dryrun']))


if __name__ == '__main__':
    main()
