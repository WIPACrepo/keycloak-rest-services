"""
Update membership of "synchronized" groups to be a subset of the union of
their source groups. This action can implement two membership policies:
"prune" and "match". Under the "prune" policy, members who don't belong to
the parent groups are pruned. The "match" policy also adds missing members,
thus making the synchronized group's memberships match that of the union
of the parent groups.

Two important additional features of this action are support for removals
deferred by a grace period and customizable email notifications.

The action has two modes of operation: "automatic" and "manual". In automatic
mode the action automatically discovers "synchronized" group, loads their
configuration from custom group attributes and updates the group's membership
according to the configured policy. The manual mode is intended for debugging
and silent initial seeding of groups. In the manual mode, automatic discovery
is disabled and certain group synchronization parameters can be overridden
from the command line.

Paths of the source groups are specified as a JSONPath expression to be
applied to the complete Keycloak group hierarchy (list of group trees,
one per top-level group, containing all groups). The JSONPath expression
uses the extended syntax that is documented here:
https://github.com/h2non/jsonpath-ng/.

Runtime configuration options are specified for each composite group as
custom group attributes. Referer to the "help" metadata attribute of
configuration parameters defined in the code for their functions. Also,
see the custom attribute documentation page at the end of the docstring.

Note that required attributes for automatic operation are:
 *_enable:
        true/false: automatic sync enabled.
 *_policy:
        prune: remove members who are not members of source groups.
        match: add/remove members so that the groups membership exactly
                matches the union of the memberships of the source groups.
 *_sources_expr:
        JSONPath expression that, when applied to the complete Keycloak
        group hierarchy yields paths of all source groups.

Originally written to automate management of some /mail/ subgroups
(mailing lists).

Custom Keycloak attributes used in this code are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.sync_synchronized_groups \
        --manual /mail/authorlist-test \
            '$..subGroups[?path == "/institutions/IceCube"]
                .subGroups[?attributes.authorlist == "true"]
                    .subGroups[?name =~ "^authorlist.*"].path' \
        --dryrun
"""

import asyncio
import logging
import sys
from attrs import define, field, fields
from datetime import datetime, timedelta
from enum import Enum
from functools import partial
from itertools import chain
from jsonpath_ng.ext import parse  # type: ignore
from rest_tools.client.client_credentials import ClientCredentialsAuth

from krs.email import send_email
from krs.groups import (get_group_membership, group_info, remove_user_group,
                        add_user_group, get_group_hierarchy, list_groups)
from krs.token import get_rest_client
from krs.users import user_info, modify_user


ACTION_ID = 'sync_synchronized_groups'
logger = logging.getLogger(ACTION_ID)
ATTR_NAME_PREFIX = f"synchronized_group_"


def _double_at_to_newline(s):
    return s.replace('@@', '\n')


def _bool_from_string(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    elif not s:
        return None
    else:
        raise ValueError(f"Couldn't parse bool from {s}")


NEWLINE_CONVERSION_HELP = "(every occurrence of @@ will be replaced with newlines)"
NOTIFICATION_APPEND_HELP = ("Append this text to the default notification template for "
                            "this event type ") + NEWLINE_CONVERSION_HELP
NOTIFICATION_OVERRIDE_HELP = ('Use this template instead of the default one for '
                              'notifications of this event type ') + NEWLINE_CONVERSION_HELP


@define
class GroupEventConfig:
    addition_occurred_notify: bool = (
        field(converter=_bool_from_string, default="true",
              metadata={'attr': ATTR_NAME_PREFIX + 'addition_occurred_notify',
                        'help': 'send email notification when a user is added '
                                'to the group'}))
    removal_pending_notify: bool = (
        field(converter=_bool_from_string, default="true",
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_pending_notify',
                        'help': 'send email notification when a user is scheduled '
                                'for removal (if grace period enabled)'}))
    removal_averted_notify: bool = (
        field(converter=_bool_from_string, default="true",
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_averted_notify',
                        'help': 'send email notification when a user is no longer '
                                'scheduled for removal (because they re-joined a '
                                'source group before the grace period expired)'}))
    removal_occurred_notify: bool = (
        field(converter=_bool_from_string, default="true",
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_occurred_notify',
                        'help': 'send email notification when a user is removed from the group'}))

    removal_pending_message_append: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_pending_message_append',
                        "help": NOTIFICATION_APPEND_HELP}))
    removal_pending_message_override: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_pending_message_override',
                        'help': NOTIFICATION_OVERRIDE_HELP}))
    removal_averted_message_append: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_averted_message_append',
                        "help": NOTIFICATION_APPEND_HELP}))
    removal_averted_message_override: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_averted_message_override',
                        'help': NOTIFICATION_OVERRIDE_HELP}))
    removal_occurred_message_append: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_occurred_message_append',
                        "help": NOTIFICATION_APPEND_HELP}))
    removal_occurred_message_override: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_occurred_message_override',
                        'help': NOTIFICATION_OVERRIDE_HELP}))
    addition_occurred_message_append: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'addition_occurred_message_append',
                        'help': NOTIFICATION_APPEND_HELP}))
    addition_occurred_message_override: str = (
        field(converter=_double_at_to_newline, default='',
              metadata={'attr': ATTR_NAME_PREFIX + 'addition_occurred_message_override',
                        "help": NOTIFICATION_OVERRIDE_HELP}))


class MembershipSyncPolicy(Enum):
    """This script's operating modes. See file docstring for details."""
    prune = 'prune'
    match = 'match'


@define
class GroupSyncCoreConfig:
    enable: bool = (
        field(converter=_bool_from_string,
              metadata={'attr': ATTR_NAME_PREFIX + 'enable',
                        'help': 'Enable/disable automatic sync.'}))
    policy: MembershipSyncPolicy = (
        field(converter=MembershipSyncPolicy,
              metadata={'attr': ATTR_NAME_PREFIX + 'policy',
                        'help': 'Membership policy. See file docstring for help.'}))
    sources_expr = (
        field(converter=lambda x: parse(x) if x else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'sources_expr',
                        'help': 'JSONPath expression for source group paths. '
                                'See file docstring for details.'}))
    removal_grace_days: int = (
        field(converter=int, default=0,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_grace_days',
                        'help': 'Number of days to delay removal of users by.'}))


class EmailTemplates:
    MESSAGE_FOOTER = """\n\n
This message was generated by the sync_synchronized_groups robot.
Please contact help@icecube.wisc.edu for support."""
    REMOVAL_AVERTED = """{username},\n
You are no longer scheduled for removal from group {group_path}.\n\n"""
    REMOVAL_PENDING = """{username},\n
You have been scheduled for removal from group {group_path}
because you are no longer a member of any of its constituent groups.
Unless you (re)join one of those groups, you will be removed
after a grace period.\n\n"""
    REMOVAL_OCCURRED = """{username},\n
You have been removed from group {group_path}
because you are not a member of any of its constituent groups.\n\n"""
    ADDITION_OCCURRED = """{username},\n
You have been added to group {group_path} because you
are a member of one of its constituent groups.\n\n"""


class GroupSyncConfig(GroupSyncCoreConfig):
    def __init__(self, group_path: str, group_attrs: dict):
        kwargs_super = {a.name: group_attrs[a.metadata['attr']]
                        for a in GroupSyncCoreConfig.__attrs_attrs__
                        if a.metadata['attr'] in group_attrs}
        super().__init__(**kwargs_super)

        kwargs_notify = {a.name: group_attrs[a.metadata['attr']]
                         for a in GroupEventConfig.__attrs_attrs__
                         if a.metadata['attr'] in group_attrs}
        self._events = GroupEventConfig(**kwargs_notify)

        self.group_path = group_path
        self.removal_scheduled_user_attr_name = f"{group_path}_removal_scheduled_at"

        self.message_addition_occurred: str = (
            '' if not self._events.addition_occurred_notify
            else self._events.addition_occurred_message_override
            or (EmailTemplates.ADDITION_OCCURRED
                + self._events.addition_occurred_message_append
                + EmailTemplates.MESSAGE_FOOTER))

        self.message_removal_pending: str = (
            '' if not self._events.removal_pending_notify
            else self._events.removal_pending_message_override
            or (EmailTemplates.REMOVAL_PENDING
                + self._events.removal_pending_message_append
                + EmailTemplates.MESSAGE_FOOTER))

        self.message_removal_averted: str = (
            '' if not self._events.removal_averted_notify
            else self._events.removal_averted_message_override
            or (EmailTemplates.REMOVAL_AVERTED
                + self._events.removal_averted_message_append
                + EmailTemplates.MESSAGE_FOOTER))

        self.message_removal_occurred: str = (
            '' if not self._events.removal_occurred_notify
            else self._events.removal_occurred_message_override
            or (EmailTemplates.REMOVAL_OCCURRED
                + self._events.removal_occurred_message_append
                + EmailTemplates.MESSAGE_FOOTER))


async def manual_sync(target_path: str,
                      source_groups_expr: str,
                      /, *,
                      keycloak_client: ClientCredentialsAuth,
                      allow_notifications: bool = False,
                      dryrun: bool = False):
    """Execute a manual sync of members of the synchronized group at `target_path`.

    The configured source group expression will be overridden with `source_groups_expr`.
    Notifications may be forced disabled with `notify`.

    Args:
        target_path (str): path to the destination composite group
        source_groups_expr (str): JSONPath expression that yields constituent group paths
                                  when applied to the complete Keycloak group hierarchy.
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        allow_notifications (bool): if False, suppress email notifications
    """
    logger.info(f"Manually syncing {target_path}")
    logger.info(f"Constituents expression: {source_groups_expr}")
    target_group = await group_info(target_path, rest_client=keycloak_client)

    cfg = GroupSyncConfig(target_path, target_group['attributes'])
    if cfg.enable:
        # noinspection PyTypeChecker
        logger.critical(f"To operate in manual mode, {target_path}'s "
                        f"{fields(GroupSyncConfig).enable.metadata['attr']} attribute must not be true.")
        return 1

    # override sources expr
    cfg.sources_expr = source_groups_expr

    return await sync_composite_group(target_path,
                                      cfg=cfg,
                                      keycloak_client=keycloak_client,
                                      allow_notifications=allow_notifications,
                                      dryrun=dryrun)


async def auto_sync(keycloak_client, dryrun):
    """Discover enabled composite groups and sync them.

    Args:
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Find all enabled composite groups. At the moment, it's much faster
    # to list all groups and pick the ones we need in python, than to query
    # custom attributes via REST API
    all_groups = await list_groups(rest_client=keycloak_client)
    # noinspection PyTypeChecker
    enabled_group_paths = [v['path'] for v in all_groups.values()
                           if v.get('attributes', {})
                           .get(fields(GroupSyncConfig).enable.metadata['attr'])]

    for enabled_group_path in enabled_group_paths:
        enabled_group = await group_info(enabled_group_path, rest_client=keycloak_client)
        cfg = GroupSyncConfig(enabled_group_path, enabled_group['attributes'])
        await sync_composite_group(enabled_group_path,
                                   cfg=cfg,
                                   keycloak_client=keycloak_client,
                                   allow_notifications=True,
                                   dryrun=dryrun)


def send_notification(user: dict, subject: str, body: str):
    username = user['username']
    user_attrs = user['attributes']
    to_address = f"{username}@icecube.wisc.edu"
    cc_addresses = filter(None, {user.get('email'), user_attrs.get('mailing_list_email')})
    logger.info(f"Sending '{subject} notification to {to_address,cc_addresses=}")
    send_email(to_address, subject, body, cc=cc_addresses)


async def process_valid_member(username: str, cfg: GroupSyncConfig, dryrun: bool, notify: bool,
                               keycloak_client: ClientCredentialsAuth):
    """Process a user who is a current group member and should not be removed."""
    # Set up partials to make the code easier to read
    _modify_user = partial(modify_user, rest_client=keycloak_client)
    _user_info = partial(user_info, rest_client=keycloak_client)

    # Reset removal grace times (will be set for valid members if they
    # rejoined a constituent group before removal grace period expired)
    user = await _user_info(username)
    user_attrs = user['attributes']
    if user_attrs.get(cfg.removal_scheduled_user_attr_name):
        logger.info(f"Clearing {username}'s {cfg.removal_scheduled_user_attr_name} ({dryrun,notify=})")
        if not dryrun:
            await _modify_user(username, attribs={cfg.removal_scheduled_user_attr_name: None})
            if notify and cfg.message_removal_averted:
                send_notification(user, f"You are no longer scheduled for removal from group {cfg.group_path}",
                                  cfg.message_removal_averted.format(
                                      username=username, group_path=cfg.group_path))


async def process_extraneous_member(username: str, cfg: GroupSyncConfig, dryrun: bool, notify: bool,
                                    keycloak_client: ClientCredentialsAuth):
    """Process a current members who does not belong to any source group."""
    # Set up partials to make the code easier to read
    _modify_user = partial(modify_user, rest_client=keycloak_client)
    _remove_user_group = partial(remove_user_group, rest_client=keycloak_client)

    logger.info(f"{username} shouldn't be in {cfg.group_path} ({dryrun,notify=})")
    user = await user_info(username, rest_client=keycloak_client)
    user_attrs = user['attributes']

    # Handle removal grace period. If unset, set and move on to next member.
    # If set to future, move on to next member. Else, fall through to removal code
    if cfg.removal_grace_days:
        if removal_scheduled_at_str := user_attrs.get(cfg.removal_scheduled_user_attr_name):
            removal_scheduled_at = datetime.fromisoformat(removal_scheduled_at_str)
            if datetime.now() < removal_scheduled_at + timedelta(days=cfg.removal_grace_days):
                logger.info(f"Too early to remove {username} {removal_scheduled_at_str=}")
                return
            else:
                logger.info(f"Removal grace period expired ({removal_scheduled_at_str,cfg.removal_grace_days=})")
        else:
            # "Removal scheduled attribute" attribute not set. Set it and move on.
            new_removal_scheduled_at_str = datetime.now().isoformat()
            logger.info(f"Setting {username}'s {cfg.removal_scheduled_user_attr_name} "
                        f"to {new_removal_scheduled_at_str} ({dryrun,notify=})")
            if not dryrun:
                await _modify_user(username, attribs={cfg.removal_scheduled_user_attr_name:
                                                      new_removal_scheduled_at_str})
                if notify and cfg.message_removal_pending:
                    send_notification(user, f"You are scheduled for removal from group {cfg.group_path}",
                                      cfg.message_removal_pending.format(
                                          username=username, group_path=cfg.group_path))
            return

    # If we are here, then either group grace period not configured or the grace
    # period expired. Clean-up and remove the user from the group.
    if user_attrs.get(cfg.removal_scheduled_user_attr_name):
        logger.info(f"Clearing {username}'s {cfg.removal_scheduled_user_attr_name} attribute ({dryrun,notify=})")
        if not dryrun:
            await _modify_user(username, attribs={cfg.removal_scheduled_user_attr_name: None})
    logger.info(f"Removing {username} from {cfg.group_path} ({dryrun,notify=}")
    if not dryrun:
        await _remove_user_group(cfg.group_path, username)
        if notify and cfg.message_removal_occurred:
            send_notification(user, f"You have been removed from group {cfg.group_path}",
                              cfg.message_removal_occurred.format(
                                  username=username, group_path=cfg.group_path))


async def process_missing_member(username: str, cfg: GroupSyncConfig, dryrun: bool, notify: bool,
                                 keycloak_client: ClientCredentialsAuth):
    """Process a user who should be group members but isn't."""
    logger.info(f"Adding {username} to {cfg.group_path} ({dryrun,notify=})")
    if dryrun:
        return
    await add_user_group(cfg.group_path, username, rest_client=keycloak_client)
    user = await user_info(username, rest_client=keycloak_client)
    if notify and cfg.message_addition_occurred:
        send_notification(user, f"You have been added to group {cfg.group_path}",
                          cfg.message_addition_occurred.format(
                              username=username, group_path=cfg.group_path))


async def sync_composite_group(target_path: str,
                               /, *,
                               cfg: GroupSyncConfig,
                               keycloak_client: ClientCredentialsAuth,
                               allow_notifications: bool,
                               dryrun: bool = False):
    """Synchronize membership of the synchronized group at `target_path`.

    `constituents_expr` is a string with JSONPath expression that will be
    applied to the complete group hierarchy to extract paths of the source
    groups.

    Although runtime configuration options are stored as the target group's
    custom attributes, this code shall not access them directly, and instead
    use the `cfg` parameter. This is to allow some options to be overridden.

    Args:
        target_path (str): path to the destination composite group
        cfg (GroupSyncConfig): runtime configuration options
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        allow_notifications (bool): if False, suppress all email notifications
    """
    # Set up partials to make the code easier to read
    _get_group_hierarchy = partial(get_group_hierarchy, rest_client=keycloak_client)
    _get_group_membership = partial(get_group_membership, rest_client=keycloak_client)

    logger.info(f"Processing composite group {target_path}")

    # Build the list of all constituent groups' paths
    group_hierarchy = await _get_group_hierarchy()
    constituent_group_paths = [v.value for v in cfg.sources_expr.find(group_hierarchy)]
    logger.debug(f"Syncing {target_path} to {constituent_group_paths}")

    # Determine what the current membership is and what it should be
    intended_members_lists = [await _get_group_membership(constituent_group_path)
                              for constituent_group_path in constituent_group_paths]
    intended_members = set(chain.from_iterable(intended_members_lists))
    current_members = set(await _get_group_membership(target_path))

    for valid_member in current_members & intended_members:
        await process_valid_member(valid_member, cfg, dryrun, allow_notifications, keycloak_client)

    for extraneous_member in current_members - intended_members:
        await process_extraneous_member(extraneous_member, cfg, dryrun, allow_notifications, keycloak_client)

    if cfg.policy == MembershipSyncPolicy.match:
        for missing_member in intended_members - current_members:
            await process_missing_member(missing_member, cfg, dryrun, allow_notifications, keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync membership of synchronized group(s) with the corresponding '
                    'source groups according to the configured policy. '
                    'See file docstring for details and examples.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument('--auto', action='store_true',
                       help='automatically discover all enabled composite groups and sync '
                            'them using configuration stored in their attributes. '
                            'See file docstring for details')
    mutex.add_argument('--manual', nargs=2, metavar=('TARGET_GROUP_PATH', 'JSONPATH_EXPR'),
                       help="sync the synchronized group at TARGET_GROUP_PATH with the "
                            "source groups produced by JSONPATH_EXPR when applied to the "
                            "complete Keycloak group hierarchy. ")
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    parser.add_argument('--allow-notifications', action='store_true',
                        help="send email notifications if using --manual; required with --auto")
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'),
                        help='application logging level')
    parser.add_argument('--log-level-client', default='warning', choices=('debug', 'info', 'warning', 'error'),
                        help='REST client logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))
    cca_logger = logging.getLogger('ClientCredentialsAuth')
    cca_logger.setLevel(getattr(logging, args['log_level_client'].upper()))

    if not args['allow_notifications'] and args['auto']:
        logger.critical("--allow-notifications is required with --auto")
        parser.exit(1)

    keycloak_client = get_rest_client()

    if args['auto']:
        return asyncio.run(auto_sync(
            keycloak_client=keycloak_client,
            dryrun=args['dryrun']))
    else:
        return asyncio.run(manual_sync(args['manual'][0],
                                       args['manual'][1],
                                       keycloak_client=keycloak_client,
                                       allow_notifications=args['notify'],
                                       dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
