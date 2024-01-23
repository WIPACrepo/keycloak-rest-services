"""
Remove from KeyCloak mailing list groups (subgroups of /mail) users who are
not members of the experiments listed in their `allow_members_from_experiments`
attributes.

Nothing is done to groups that don't define `allow_members_from_experiments`.

Users that have recently changed institutions will be granted the specified grace
period to avoid removal of users who are in the midst of changing institutions
(i.e. when a user is already removed from institution A but before their request
to be added to institution B has been approved).

This code relies on the `institutions_last_seen` and `institutions_last_changed`
user attributes, and, consequently, on the Keycloak Rest Services action that
updates those attributes. Users that don't have `institutions_last_seen` defined
are assumed to belong to no institution.

Users can optionally be notified of changes via email. SMTP server is
controlled by the EMAIL_SMTP_SERVER environmental variable and defaults
to localhost. See krs/email.py for more email options.

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

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
from krs.email import send_email

logger = logging.getLogger('deprovision_mailing_lists')

MESSAGE_FOOTER = "\n\nThis message was generated by the deprovision_mailing_lists robot."

REMOVAL_MESSAGE = "You have been removed from group {group_path} because you do not meet " \
                  "the requirement of being a member of an institution belonging to " \
                  "{experiments} experiment(s)." + MESSAGE_FOOTER


async def _deprovision_group(group_path, removal_grace_days, allowed_institutions,
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


async def deprovision_mailing_list_groups(removal_grace_days, single_group,
                                          send_notifications, keycloak_client, dryrun=False):
    """Remove from all mailing list groups (subgroups of /mail), and their
    _admin subgroups, the users who are not members of the experiments listed
    in the `allow_members_from_experiments` attributes of those groups. Users
    that have recently changed institutions will be granted the given grace
    period before removal. Optionally, notify users. Relies on user attributes
    `institutions_last_seen` and `institutions_last_changed`.

    Args:
        removal_grace_days (int): delay of user removal
        single_group (str): only consider this group instead of all groups
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
        allowed_experiments = ml_group['attributes'].get('allow_members_from_experiments')
        if not allowed_experiments:
            logger.warning(f"Skipping {ml_group['path']} because allow_members_from_experiments is missing or empty")
            continue
        if not isinstance(allowed_experiments, list):
            allowed_experiments = [allowed_experiments]

        allowed_institutions = set()
        for experiment in allowed_experiments:
            insts = await list_insts(experiment, rest_client=keycloak_client)
            allowed_institutions.update(insts.keys())

        removed_users = await _deprovision_group(ml_group['path'], removal_grace_days,
                                                 allowed_institutions, user_info_cache,
                                                 keycloak_client, dryrun)
        if [sg for sg in ml_group['subGroups'] if sg['name'] == '_admin']:
            removed_users.extend(await _deprovision_group(ml_group['path'] + '/_admin',
                                                          removal_grace_days, allowed_institutions,
                                                          user_info_cache, keycloak_client, dryrun))

        for username in removed_users:
            logger.info(f"Notifying {username} of removal from {ml_group['path']}"
                        f"(send_notifications={send_notifications})")
            if not dryrun and send_notifications:
                send_email(username + '@icecube.wisc.edu',
                           f"You have been removed from {ml_group['path']}",
                           REMOVAL_MESSAGE.format(
                               group_path=ml_group['path'],
                               experiments=' '.join(allowed_experiments)),
                           headline="IceCube Mailing List Management")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove from KeyCloak mailing list groups users who are not part of '
                    'those lists\' allowed institutions/experiments/projects. See file '
                    'docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--removal-grace', metavar='DAYS', default=3, type=int,
                        help='how much to delay removal of institutionless users')
    parser.add_argument('--send-notifications', action='store_true',
                        help='send email notifications to users')
    parser.add_argument('--single-group', metavar='NAME',
                        help='only consider group NAME')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'),
                        help='logging level')
    parser.add_argument('--dryrun', action='store_true', help='dry run')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(deprovision_mailing_list_groups(
        args['removal_grace'],
        args['single_group'],
        args['send_notifications'],
        keycloak_client,
        args['dryrun']))


if __name__ == '__main__':
    main()
