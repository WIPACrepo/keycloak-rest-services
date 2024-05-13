"""
Update membership of "synchronized" groups to be a subset of the union of
their source groups. This action can implement two membership policies:
"prune" and "match". Under the "prune" policy, members who don't belong to
the parent groups are pruned. The "match" policy prunes extraneous members
and also adds missing members, thus making the membership of the group match
that of the union of the parent groups.

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

Note that the required attributes for automatic operation are:
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
            "$..subGroups[?path == '/institutions/IceCube']
                .subGroups[?attributes.authorlist == 'true']
                    .subGroups[?name =~ '^authorlist.*'].path" \
        --dryrun
"""

import asyncio
import json
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
                        add_user_group, get_group_hierarchy, list_groups, modify_group)
from krs.token import get_rest_client
from krs.users import user_info


ACTION_ID = 'sync_synchronized_groups'
logger = logging.getLogger(ACTION_ID)


# Hide stuff from the global structure view and autocomplete
class GrpCfgRes:
    ATTR_NAME_PREFIX = f"synchronized_group_"
    NEWLINE_CONVERSION_HELP = "(every occurrence of @@ will be replaced with newlines)"
    NOTIFICATION_APPEND_HELP = ("Append this text to the default notification template for "
                                "this event type ") + NEWLINE_CONVERSION_HELP
    NOTIFICATION_OVERRIDE_HELP = ('Use this template instead of the default one for '
                                  'notifications of this event type ') + NEWLINE_CONVERSION_HELP

    @classmethod
    def double_at_to_newline(cls, s):
        return s.replace('@@', '\n')

    @classmethod
    def bool_from_string(cls, s):
        if s.lower() == 'true':
            return True
        elif s.lower() == 'false':
            return False
        elif not s:
            return None
        else:
            raise ValueError(f"Couldn't parse bool from {s}")


@define
class GroupEventConfig:
    addition_occurred_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_notify',
                        'help': 'send email notification when a user is added '
                                'to the group'}))
    removal_pending_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_notify',
                        'help': 'send email notification when a user is scheduled '
                                'for removal (if grace period enabled)'}))
    removal_averted_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_notify',
                        'help': 'send email notification when a user is no longer '
                                'scheduled for removal (because they re-joined a '
                                'source group before the grace period expired)'}))
    removal_occurred_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_notify',
                        'help': 'send email notification when a user is removed from the group'}))

    removal_pending_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_pending_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_averted_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_averted_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_occurred_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_occurred_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    addition_occurred_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_message_append',
                        'help': GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    addition_occurred_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_message_override',
                        "help": GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))


class MembershipSyncPolicy(Enum):
    """This script's operating modes. See file docstring for details."""
    prune = 'prune'
    match = 'match'


@define
class GroupSyncCoreConfig:
    enable: bool = (
        field(converter=GrpCfgRes.bool_from_string,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'enable',
                        'help': 'Enable/disable automatic sync.'}))
    policy: MembershipSyncPolicy = (
        field(converter=MembershipSyncPolicy,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'policy',
                        'help': 'Membership policy. See file docstring for help.'}))
    sources_expr = (
        field(converter=lambda x: parse(x) if x else None, default=None,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'sources_expr',
                        'help': 'JSONPath expression for source group paths. '
                                'See file docstring for details.'}))
    removal_grace_days: int = (
        field(converter=int, default=0,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_grace_days',
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
        self.deferred_removals_attr = GrpCfgRes.ATTR_NAME_PREFIX + "deferred_removals"

        self.message_addition_occurred: str = (
            '' if not self._events.addition_occurred_notify
            else self._events.addition_occurred_message_override + EmailTemplates.MESSAGE_FOOTER
            or (EmailTemplates.ADDITION_OCCURRED
                + self._events.addition_occurred_message_append
                + EmailTemplates.MESSAGE_FOOTER))

        self.message_removal_pending: str = (
            '' if not self._events.removal_pending_notify
            else self._events.removal_pending_message_override + EmailTemplates.MESSAGE_FOOTER
            or (EmailTemplates.REMOVAL_PENDING
                + self._events.removal_pending_message_append
                + EmailTemplates.MESSAGE_FOOTER))

        self.message_removal_averted: str = (
            '' if not self._events.removal_averted_notify
            else self._events.removal_averted_message_override + EmailTemplates.MESSAGE_FOOTER
            or (EmailTemplates.REMOVAL_AVERTED
                + self._events.removal_averted_message_append
                + EmailTemplates.MESSAGE_FOOTER))

        self.message_removal_occurred: str = (
            '' if not self._events.removal_occurred_notify
            else self._events.removal_occurred_message_override + EmailTemplates.MESSAGE_FOOTER
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

    return await sync_synchronized_group(target_path,
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
        await sync_synchronized_group(enabled_group_path,
                                      cfg=cfg,
                                      keycloak_client=keycloak_client,
                                      allow_notifications=True,
                                      dryrun=dryrun)


def send_notification(user: dict, subject: str, body: str):
    username = user['username']
    user_attrs = user['attributes']
    to_address = f"{username}@icecube.wisc.edu"
    cc_addresses = list(filter(None, {user.get('email'), user_attrs.get('mailing_list_email')}))
    logger.info(f"Sending '{subject} notification to {to_address,cc_addresses=}")
    send_email(to_address, subject, body, cc=cc_addresses)


async def process_valid_member(username: str, cfg: GroupSyncConfig, dryrun: bool, notify: bool,
                               keycloak_client: ClientCredentialsAuth):
    """Process a user who is a current group member and should not be removed."""
    # Reset removal grace times (will be set for valid members if they
    # rejoined a constituent group before removal grace period expired)
    group = await group_info(cfg.group_path, rest_client=keycloak_client)
    group_attrs = group.get('attributes', {})
    deferred_removals: dict = json.loads(group_attrs.get(cfg.deferred_removals_attr, '{}'))
    if deferred_removals.get(username):
        logger.info(f"Removing valid {username} from deferred removal state({dryrun,notify=})")
        if not dryrun:
            deferred_removals.pop(username)
            await modify_group(cfg.group_path, rest_client=keycloak_client,
                               attrs={cfg.deferred_removals_attr: json.dumps(deferred_removals)})
            logger.info(f"New deferred removal state: {deferred_removals}")
            if notify and cfg.message_removal_averted:
                user = await user_info(username, rest_client=keycloak_client)
                send_notification(user, f"You are no longer scheduled for removal from group {cfg.group_path}",
                                  cfg.message_removal_averted.format(
                                      username=username, group_path=cfg.group_path))


async def process_extraneous_member(username: str, cfg: GroupSyncConfig, dryrun: bool, notify: bool,
                                    keycloak_client: ClientCredentialsAuth):
    """Process a current member who doesn't belong to any source group."""
    # Set up partials to make the code easier to read
    _group_info = partial(group_info, rest_client=keycloak_client)
    _modify_group = partial(modify_group, rest_client=keycloak_client)
    _remove_user_group = partial(remove_user_group, rest_client=keycloak_client)

    logger.info(f"{username} shouldn't be in {cfg.group_path} ({dryrun,notify=})")
    group = await _group_info(cfg.group_path)
    group_attrs = group.get('attributes', {})
    deferred_removals: dict = json.loads(group_attrs.get(cfg.deferred_removals_attr, '{}'))

    # Handle removal grace period. If unset, set and move on to next member.
    # If set to future, move on to next member. Else, fall through to removal code
    if cfg.removal_grace_days:
        if removal_scheduled_at_str := deferred_removals.get(username):
            removal_scheduled_at = datetime.fromisoformat(removal_scheduled_at_str)
            if datetime.now() < removal_scheduled_at + timedelta(days=cfg.removal_grace_days):
                logger.info(f"Too early to remove {username} {removal_scheduled_at_str=}")
                return
            else:
                logger.info(f"Removal grace period expired ({removal_scheduled_at_str,cfg.removal_grace_days=})")
        else:
            # "Removal scheduled attribute" attribute not set. Set it and move on.
            new_removal_scheduled_at_str = datetime.now().isoformat()
            logger.info(f"Adding {username} to deferred removals {new_removal_scheduled_at_str} ({dryrun,notify=})")
            if not dryrun:
                deferred_removals[username] = new_removal_scheduled_at_str
                await _modify_group(cfg.group_path, attrs={
                    cfg.deferred_removals_attr: json.dumps(deferred_removals)
                })
                logger.info(f"New deferred removal state: {deferred_removals}")
                if notify and cfg.message_removal_pending:
                    user = await user_info(username, rest_client=keycloak_client)
                    send_notification(user, f"You are scheduled for removal from group {cfg.group_path}",
                                      cfg.message_removal_pending.format(
                                          username=username, group_path=cfg.group_path))
            return

    # If we are here, then either group grace period not configured or the grace
    # period expired. Clean-up and remove the user from the group.
    if deferred_removals.get(username):
        logger.info(f"Removing {username} from deferred removal state({dryrun,notify=})")
        if not dryrun:
            deferred_removals.pop(username)
            await _modify_group(cfg.group_path, attrs={
                cfg.deferred_removals_attr: json.dumps(deferred_removals)
            })
            logger.info(f"New deferred removal state: {deferred_removals}")
    logger.info(f"Removing extraneous {username} from {cfg.group_path} ({dryrun,notify=}")
    if not dryrun:
        await _remove_user_group(cfg.group_path, username)
        if notify and cfg.message_removal_occurred:
            user = await user_info(username, rest_client=keycloak_client)
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


async def sync_synchronized_group(target_path: str,
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
    logger.info(f"Processing composite group {target_path}")

    # Build the list of all constituent groups' paths
    group_hierarchy = await get_group_hierarchy(rest_client=keycloak_client)
    constituent_group_paths = [v.value for v in cfg.sources_expr.find(group_hierarchy)]
    logger.debug(f"Syncing {target_path} to {constituent_group_paths}")

    # Determine what the current membership is and what it should be
    intended_members_lists = [await get_group_membership(constituent_group_path, rest_client=keycloak_client)
                              for constituent_group_path in constituent_group_paths]
    intended_members = set(chain.from_iterable(intended_members_lists))
    current_members = set(await get_group_membership(target_path, rest_client=keycloak_client))

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
        target_group, source_group_expr = args['manual']
        return asyncio.run(manual_sync(target_group,
                                       source_group_expr,
                                       keycloak_client=keycloak_client,
                                       allow_notifications=args['allow_notifications'],
                                       dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
