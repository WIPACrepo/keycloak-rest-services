# noinspection GrazieInspection
"""
If you change this code, please also update the user documentation of
synchronized groups: https://bookstack.icecube.wisc.edu/ops/books/keycloak-user-management/page/synchronized-groups

Update membership of "synchronized" groups (i.e. groups managed by this
script) to be a subset of the union of their "source" groups. This action
can implement two membership policies: "prune" and "match". Under the "prune"
policy, members who don't belong to the source groups are pruned. The "match"
policy prunes extraneous members and also adds missing members, thus making
the membership of the group match that of the union of the source groups.

This script has two modes of operation: "automatic" and "manual". In automatic
mode the script automatically discovers all enabled "synchronized" groups,
loads their configuration from custom group attributes and updates the group's
membership according to the configured policy. The manual mode is intended for
debugging and silent initial seeding of groups. In the manual mode, automatic
discovery is disabled and certain group synchronization parameters can be
overridden from the command line.

Two important additional features of this action are the support for optionally
deferring removals by a grace period and optionally customizing email notifications.
Note that by default notifications are enabled and there is no removal grace period.

Runtime configuration options are specified for each synchronized group as
custom group attributes. Use the command line flag --configuration-help
[ref:ooK1Ua1B] to see all available configuration options. Not

Paths of the source groups are specified as a JSONPath expression that yields
group paths when applied to the complete Keycloak group hierarchy (list of
group trees, one per top-level group, containing all groups). The JSONPath
expression uses the extended syntax that is documented here:
https://github.com/h2non/jsonpath-ng/. There are some examples of typical
JSONPaths below.


This code was originally written to automate management of some /mail/
subgroups (mailing lists).

Custom Keycloak attributes used in this code are also documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes
Please update that page if you make changes to configuration options.

Examples::
    # Getting help on how to configure synchronized groups
    python -m actions.sync_synchronized_groups --configuration-help         # ref:ooK1Ua1B

    # Simple JSONPath defining source groups by path regular expression
    python -m actions.sync_synchronized_groups \
        --manual /path/to/group/composite-group \
            "$..subGroups[?path =~ '/path/to/parent/(constituent-1|constituent-2)'].path" \
        --dryrun                                                            # ref:so5X1opu

    # More complex JSONPath defining source groups based on group
    # attribute values
    python -m actions.sync_synchronized_groups \
        --manual /mail/authorlist-test \
            "$..subGroups[?path == '/institutions/IceCube']
                .subGroups[?attributes.authorlist == 'true']
                    .subGroups[?name =~ '^authorlist.*'].path" \
        --dryrun                                                            # ref:so5X1opu
"""

import asyncio
import json
import logging
import re
import string
import sys
from asyncache import cached  # type: ignore
from attrs import define, field, fields, NOTHING
from cachetools import Cache
from datetime import datetime, timedelta
from enum import Enum
from itertools import chain
from jsonpath_ng.ext import parse  # type: ignore
from jsonpath_ng.exceptions import JsonPathParserError
from rest_tools.client.client_credentials import ClientCredentialsAuth

from krs.email import send_email
from krs.groups import (get_group_membership, group_info, remove_user_group,
                        add_user_group, get_group_hierarchy, list_groups, modify_group)
from krs.token import get_rest_client
from krs.users import user_info

ACTION_ID = "sync_synchronized_groups"
logger = logging.getLogger(f'{ACTION_ID}')


@cached(Cache(maxsize=10000))
async def user_info_cached(username, keycloak):
    return await user_info(username, rest_client=keycloak)


@cached(Cache(maxsize=10000))
async def group_info_cached(group_path, keycloak):
    return await group_info(group_path, rest_client=keycloak)


@cached(Cache(maxsize=10000))
async def get_group_membership_cached(group_path, keycloak):
    return await get_group_membership(group_path, rest_client=keycloak)


@cached(Cache(maxsize=10000))
async def get_group_hierarchy_cached(keycloak):
    return await get_group_hierarchy(rest_client=keycloak)


# Hide stuff from the global structure view and autocomplete
class GrpCfgRes:
    ATTR_NAME_PREFIX = "synchronized_group_"
    MSG_HELP_FOOTER = ("Every @@ will be replaced with a newline. Text can be a python f-string;"
                       " see code for supported fields. Standard footer will be appended. Default: ''.")
    NOTIFICATION_APPEND_HELP = (f"Append this text to the default notification template for"
                                f" this event type. {MSG_HELP_FOOTER}")
    NOTIFICATION_OVERRIDE_HELP = (f'Optional. Use this template instead of the default one for'
                                  f' notifications of this event type. {MSG_HELP_FOOTER}')

    # Converter functions. Don't want to use lambdas since they
    # have no names, and we want to provide more meaningful messages
    # on conversion failures.
    @classmethod
    def double_at_to_newline(cls, s):
        return s.replace('@@', '\n')

    @classmethod
    def bool_from_string(cls, s):
        if s.strip().lower() == 'true':
            return True
        elif s.strip().lower() == 'false':
            return False
        elif not s:
            return None
        else:
            raise ValueError(f"Couldn't parse bool from {s}")

    @classmethod
    def parse_jsonpath(cls, jsonpath_str):
        return parse(jsonpath_str) if jsonpath_str is not None else None


@define
class SyncGroupEventConfig:
    addition_occurred_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_notify',
                        'help': 'Send email notification when a user is added '
                                'to the group. Default: true.'}))
    removal_pending_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_notify',
                        'help': 'Send email notification when a user is scheduled '
                                'for removal (if grace period enabled). Default: true.'}))
    removal_averted_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_notify',
                        'help': 'send email notification when a user is no longer scheduled '
                                'for removal (because they re-joined a source group before '
                                'the grace period expired). Default: true.'}))
    removal_occurred_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_notify',
                        'help': 'send email notification when a user is removed from the group '
                                'Default: true.'}))

    removal_pending_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_pending_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_averted_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_averted_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_occurred_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_occurred_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    addition_occurred_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_message_append',
                        'help': GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    addition_occurred_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_message_override',
                        "help": GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))


class MembershipSyncPolicy(Enum):
    """This script's operating modes. See file docstring for details."""
    prune = 'prune'
    match = 'match'


@define
class SyncGroupCoreConfig:
    auto_sync: bool = (
        field(converter=GrpCfgRes.bool_from_string,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'auto_sync_enable',
                        'help': 'Enable/disable automatic sync. Choices: true, false. Required.'}))
    policy: MembershipSyncPolicy = (
        field(converter=MembershipSyncPolicy,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'sync_policy',
                        'help': f'Membership sync policy. Choices: '
                                f'{MembershipSyncPolicy.prune.value}, {MembershipSyncPolicy.match.value}.'
                                f' If "{MembershipSyncPolicy.prune.value}": remove members not'
                                f' in source groups. If "{MembershipSyncPolicy.match.value}":'
                                f' make the membership match the union of source groups. Required.'}))
    sources_expr = (
        field(converter=GrpCfgRes.parse_jsonpath,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'source_group_paths_expr',
                        'help': 'JSONPath expression that produces source group paths when'
                                ' applied to the complete group hierarchy. See file docstring'
                                ' for details and examples. Required.'}))
    removal_grace_days: int = (
        field(converter=int, default=0,
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_grace_days',
                        'help': 'Number of days by which to delay the removal of users no longer'
                                ' in source groups. Default: 0.'}))


class EmailTemplates:
    MESSAGE_FOOTER = f"""\n\n
This message was generated by the {ACTION_ID} robot.
Please contact help@icecube.wisc.edu for support."""
    ADDITION_OCCURRED = """{username},\n
You have been automatically added to group {group_path} because you
are a member of one of its constituent groups.\n\n"""
    REMOVAL_PENDING = """{username},\n
You have been scheduled for automatic removal from group {group_path}
because you are no longer a member in any of its prerequisite groups.\n\n"""
    REMOVAL_AVERTED = """{username},\n
You are no longer scheduled for removal from group {group_path}.\n\n"""
    REMOVAL_OCCURRED = """{username},\n
You have been automatically removed from group {group_path}
because you are not a member of any of its prerequisite groups.\n\n"""


class SyncGroupConfigAttributeError(Exception):
    pass


class SyncGroupConfigValueError(Exception):
    pass


class SyncGroupConfig(SyncGroupCoreConfig):
    @staticmethod
    def _validate_required_fields(attrs_cls, field_names):
        missing_fields = []
        # noinspection PyTypeChecker
        for fld in fields(attrs_cls):
            if fld.name not in field_names and fld.default == NOTHING:
                missing_fields.append(fld)
        if missing_fields:
            raise SyncGroupConfigAttributeError(
                "Missing required attributes",
                [(fld.name, fld.metadata['attr'])
                 for fld in missing_fields])

    @staticmethod
    def _validate_field_conversions(attrs_cls, field_kwargs):
        failed_conversions = []
        # noinspection PyTypeChecker
        for fld in fields(attrs_cls):
            if fld.name in field_kwargs and fld.converter:
                try:
                    fld.converter(field_kwargs[fld.name])
                except Exception as exc:
                    failed_conversions.append(
                        (fld.name, fld.metadata["attr"], fld.converter.__func__.__qualname__,
                         field_kwargs[fld.name], type(exc), exc.args))
        if failed_conversions:
            raise SyncGroupConfigValueError("Invalid attribute values", failed_conversions)

    def __init__(self, group_path: str, group_attrs: dict):
        kwargs_super = {attr.name: group_attrs[attr.metadata['attr']]
                        for attr in SyncGroupCoreConfig.__attrs_attrs__
                        if attr.metadata['attr'] in group_attrs}
        self._validate_required_fields(SyncGroupCoreConfig, kwargs_super)
        self._validate_field_conversions(SyncGroupCoreConfig, kwargs_super)
        super().__init__(**kwargs_super)

        kwargs_notify = {attr.name: group_attrs[attr.metadata['attr']]
                         for attr in SyncGroupEventConfig.__attrs_attrs__
                         if attr.metadata['attr'] in group_attrs}
        self._validate_required_fields(SyncGroupEventConfig, kwargs_notify)
        self._validate_field_conversions(SyncGroupEventConfig, kwargs_notify)
        self._events = SyncGroupEventConfig(**kwargs_notify)

        self.group_path = group_path
        self.deferred_removals_attr = GrpCfgRes.ATTR_NAME_PREFIX + "deferred_removals"
        # noinspection PyTypeChecker
        self.sources_expr_str = group_attrs[fields(SyncGroupCoreConfig).sources_expr.metadata['attr']]
        self._deferred_removals_cache = None

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

    async def get_deferred_removals(self, keycloak: ClientCredentialsAuth) -> dict:
        if self._deferred_removals_cache is None:
            group: dict = await group_info(self.group_path, rest_client=keycloak)
            group_attrs: dict = group.get('attributes', {})
            deferred_removals_raw: dict = json.loads(group_attrs.get(self.deferred_removals_attr, '{}'))
            self._deferred_removals_cache = dict((user, datetime.fromisoformat(ts))
                                                 for user, ts in deferred_removals_raw.items())
        return self._deferred_removals_cache

    async def set_deferred_removal(self, username: str, keycloak: ClientCredentialsAuth):
        deferred_removals = await self.get_deferred_removals(keycloak)
        new_deferred_removal_str = datetime.now().isoformat()
        logger.info(f"Setting {username}'s removal timestamp to {new_deferred_removal_str}")
        deferred_removals[username] = new_deferred_removal_str
        deferred_removals_json = json.dumps(deferred_removals)
        self._deferred_removals_cache = None
        await modify_group(self.group_path, rest_client=keycloak,
                           attrs={self.deferred_removals_attr: deferred_removals_json})

    async def clear_deferred_removal(self, username: str, keycloak: ClientCredentialsAuth):
        deferred_removals = await self.get_deferred_removals(keycloak)
        if deferred_removals.pop(username, None):
            deferred_removals_json = json.dumps(deferred_removals)
            self._deferred_removals_cache = None
            await modify_group(self.group_path, rest_client=keycloak,
                               attrs={self.deferred_removals_attr: deferred_removals_json})
            logger.info(f"New deferred removal record: {deferred_removals}")


async def manual_sync(target_path: str,
                      source_groups_expr: str,
                      /, *,
                      keycloak_client: ClientCredentialsAuth,
                      allow_notifications: bool = False,
                      dryrun: bool = False):
    """Execute a manual sync of members of the synchronized group at `target_path`.

    The configured source group expression will be overridden with `source_groups_expr`.
    Notifications may be forced disabled with `allow_notifications`.

    Args:
        target_path (str): path to the target synchronized group
        source_groups_expr (str): JSONPath expression that yields constituent group paths
                                  when applied to the complete Keycloak group hierarchy.
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        allow_notifications (bool): if False, suppress email notifications
        dryrun (bool): perform a trial run with no changes made
    """
    logger.info(f"Manually syncing {target_path}")
    logger.info(f"Constituents expression: {source_groups_expr}")
    target_group = await group_info(target_path, rest_client=keycloak_client)
    target_group_attrs = target_group.get('attributes', {})

    # override sources expression
    # noinspection PyTypeChecker
    source_groups_expr_attr = fields(SyncGroupConfig).sources_expr.metadata['attr']
    target_group_attrs[source_groups_expr_attr] = source_groups_expr

    try:
        cfg = SyncGroupConfig(target_path, target_group_attrs)
    except (SyncGroupConfigAttributeError, SyncGroupConfigValueError) as exc:
        logger.error(f"{target_path} configuration exception {exc!r}")
        return 1

    if cfg.auto_sync:
        # noinspection PyTypeChecker
        logger.critical(f"To operate in manual mode, {target_path}'s "
                        f"{fields(SyncGroupConfig).auto_sync.metadata['attr']} attribute must not be true.")
        return 1
    try:
        cfg.sources_expr = source_groups_expr
    except JsonPathParserError:
        logger.critical(f"Invalid JSONPath {source_groups_expr}")
        return 1
    return await sync_synchronized_group(target_path,
                                         cfg=cfg,
                                         keycloak=keycloak_client,
                                         allow_notifications=allow_notifications,
                                         dryrun=dryrun)


async def auto_sync(keycloak_client, dryrun):
    """Discover enabled synchronized groups and sync them.

    Args:
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Find all enabled synchronized groups. At the moment, it's much faster
    # to list all groups and pick the ones we need in python, compared to
    # querying custom attributes via REST API
    all_groups = await list_groups(rest_client=keycloak_client)
    # noinspection PyTypeChecker
    auto_sync_attr = fields(SyncGroupConfig).auto_sync.metadata['attr']
    enabled_group_paths = [group['path'] for group in all_groups.values()
                           if group.get('attributes', {})
                           .get(auto_sync_attr, '').lower() == "true"]
    logger.info(f"Discovered enabled groups: {enabled_group_paths}")

    for enabled_group_path in enabled_group_paths:
        enabled_group = await group_info(enabled_group_path, rest_client=keycloak_client)
        try:
            cfg = SyncGroupConfig(enabled_group_path, enabled_group['attributes'])
        except (SyncGroupConfigAttributeError, SyncGroupConfigValueError) as exc:
            logger.error(f"{enabled_group_path} configuration exception {exc!r}")
            continue

        await sync_synchronized_group(enabled_group_path,
                                      cfg=cfg,
                                      keycloak=keycloak_client,
                                      allow_notifications=True,
                                      dryrun=dryrun)


async def send_notification(username: str, subject: str, body: str, keycloak: ClientCredentialsAuth):
    user = await user_info_cached(username, keycloak)
    user_attrs = user['attributes']
    to_address = f"{username}@icecube.wisc.edu"
    cc_addresses = list(filter(None, {user.get('email'), user_attrs.get('mailing_list_email')}))
    logger.info(f"Sending '{subject} notification to {to_address,cc_addresses=}")
    send_email(to_address, subject, body, cc=cc_addresses)


async def clear_deferred_removal(username: str, cfg: SyncGroupConfig, dryrun: bool,
                                 notify: bool, keycloak: ClientCredentialsAuth):
    """Remove a user from the deferred removal records """
    deferred_removals: dict = await cfg.get_deferred_removals(keycloak)
    if deferred_removals.get(username):
        logger.info(f"Removing {username} from deferred removal state({dryrun,notify=})")
        if not dryrun:
            await cfg.clear_deferred_removal(username, keycloak)
            logger.info(f"New deferred removal state: {await cfg.get_deferred_removals(keycloak)}")
            if notify and cfg.message_removal_averted:
                await send_notification(
                    username=username, keycloak=keycloak,
                    subject=f"You are no longer scheduled for removal from group {cfg.group_path}",
                    body=cfg.message_removal_averted.format(username=username, group_path=cfg.group_path))


async def grace_period_set_check(username: str, cfg: SyncGroupConfig, dryrun: bool,
                                 notify: bool, keycloak: ClientCredentialsAuth) -> bool:
    """Set and/or check whether the user passes grace period check

    Assumes removal grace period is enabled and non-zero.
    Sets deferred removal state if missing.

    Return:
        (bool) whether the user's removal grace period has expired
    """
    deferred_removals = await cfg.get_deferred_removals(keycloak)

    if removal_scheduled_at := deferred_removals.get(username):
        if datetime.now() < removal_scheduled_at + timedelta(days=cfg.removal_grace_days):
            return True
        else:
            logger.info(f"Removal grace period of {username} expired ({removal_scheduled_at,cfg.removal_grace_days=})")
            return False
    else:
        # Grace period configured but "removal scheduled" not set. Set it.
        if not dryrun:
            await cfg.set_deferred_removal(username, keycloak)
            if notify and cfg.message_removal_pending:
                await send_notification(
                    username=username, keycloak=keycloak,
                    subject=f"You are scheduled for removal from group {cfg.group_path}",
                    body=cfg.message_removal_pending.format(username=username, group_path=cfg.group_path))
        # We are assuming that this function is called
        # only if grace period is non-zero
        return True


async def remove_extraneous_member(username: str, cfg: SyncGroupConfig, dryrun: bool, notify: bool,
                                   keycloak: ClientCredentialsAuth):
    """Removes an extraneous member"""
    logger.info(f"Removing {username} from deferred removal state({dryrun,notify=})")
    if not dryrun:
        await cfg.clear_deferred_removal(username, keycloak)
    logger.info(f"Removing extraneous {username} from {cfg.group_path} ({dryrun,notify=}")
    if not dryrun:
        await remove_user_group(cfg.group_path, username, rest_client=keycloak)
        if notify and cfg.message_removal_occurred:
            await send_notification(
                username=username, keycloak=keycloak,
                subject=f"You have been removed from group {cfg.group_path}",
                body=cfg.message_removal_occurred.format(username=username, group_path=cfg.group_path))


async def add_missing_member(username: str, cfg: SyncGroupConfig, dryrun: bool, notify: bool,
                             keycloak: ClientCredentialsAuth):
    """Add a user who should be group members but isn't."""
    logger.info(f"Adding {username} to {cfg.group_path} ({dryrun,notify=})")
    if dryrun:
        return
    await add_user_group(cfg.group_path, username, rest_client=keycloak)
    if notify and cfg.message_addition_occurred:
        await send_notification(
            username=username, keycloak=keycloak,
            subject=f"You have been added to group {cfg.group_path}",
            body=cfg.message_addition_occurred.format(username=username, group_path=cfg.group_path))


async def sync_synchronized_group(target_path: str,
                                  /, *,
                                  cfg: SyncGroupConfig,
                                  keycloak: ClientCredentialsAuth,
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
        target_path (str): path to the target synchronized group
        cfg (SyncGroupConfig): runtime configuration options
        keycloak (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        allow_notifications (bool): if False, suppress all email notifications
    """
    # Set up partials to make the code easier to read
    logger.info(f"Processing synchronized group {target_path}")

    # noinspection PyCallingNonCallable
    group_hierarchy = await get_group_hierarchy_cached(keycloak)
    constituent_group_paths = [v.value for v in cfg.sources_expr.find(group_hierarchy)]
    if not all(isinstance(path, str)
               and re.match(f'(/[^/{string.whitespace}]+)+$', path)
               for path in constituent_group_paths):
        logger.error("Results of sources expression don't look like group paths:")
        logger.error(f"{cfg.sources_expr_str = }")
        logger.error(f"{str(constituent_group_paths)[:200] = }")
        return 1  # XXX put in tests?
    logger.info(f"Syncing {target_path} to {constituent_group_paths}")

    # Determine what the current membership is and what it should be.
    # Note on caching: it's possible for a synchronized group to be a
    # constituent of another synchronized group, and therefore change
    # during execution of this script. This is OK since this will be rare
    # and membership updates will eventually happen on a later run.
    intended_members_lists = [await get_group_membership_cached(constituent_group_path, keycloak)
                              for constituent_group_path in constituent_group_paths]
    intended_members = set(chain.from_iterable(intended_members_lists))
    current_members = set(await get_group_membership(target_path, rest_client=keycloak))

    # Process current users who are legitimate, authorized members
    for valid_member in current_members & intended_members:
        # Valid users may need to be removed from the deferred removal record
        # if they rejoined a constituent group before the grace period expired
        await clear_deferred_removal(valid_member, cfg, dryrun, allow_notifications, keycloak)

    # Prune extraneous members
    for extraneous_member in current_members - intended_members:
        if cfg.removal_grace_days:
            if await grace_period_set_check(extraneous_member, cfg, dryrun, allow_notifications, keycloak):
                continue
        await remove_extraneous_member(extraneous_member, cfg, dryrun, allow_notifications, keycloak)

    # Add missing members if policy is to match union of membership of constituents
    if cfg.policy == MembershipSyncPolicy.match:
        for missing_member in intended_members - current_members:
            await add_missing_member(missing_member, cfg, dryrun, allow_notifications, keycloak)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync membership of synchronized group(s) with the corresponding '
                    'source groups according to the configured policy. '
                    'See file docstring for details and examples.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    mutex = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--configuration-help', action='store_true',  # ref:ooK1Ua1B
                        help="display help on group configuration attributes and exit")
    mutex.add_argument('--auto', action='store_true',
                       help='automatically discover all enabled synchronized groups and sync '
                            'them using configuration stored in their attributes. '
                            'See file docstring for details')
    mutex.add_argument('--manual', nargs=2, metavar=('TARGET_GROUP_PATH', 'JSONPATH_EXPR'),  # ref:so5X1opu
                       help="sync the synchronized group at TARGET_GROUP_PATH with the "
                            "source groups produced by JSONPATH_EXPR when applied to the "
                            "complete Keycloak group hierarchy. ")
    parser.add_argument('--allow-notifications', action='store_true',
                        help="send email notifications if using --manual; required with --auto")
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'),
                        help='application logging level')
    parser.add_argument('--log-level-client', default='warning', choices=('debug', 'info', 'warning', 'error'),
                        help='REST client logging level')
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')

    args = vars(parser.parse_args())

    if args['configuration_help']:
        from textwrap import wrap
        print("\n\033[4;7m" + "Core configuration attributes:".upper() + "\033[0m\n")
        # noinspection PyTypeChecker
        for f in fields(SyncGroupCoreConfig):
            print(f"\033[3m{f.metadata['attr']}\033[0m")
            print('\n'.join('    ' + line for line in wrap(f.metadata['help'])) + '\n')

        print("\n\033[4;7m" + "Attributes configuring notifications:".upper() + "\033[0m\n")
        # noinspection PyTypeChecker
        for f in fields(SyncGroupEventConfig):
            print(f"\033[3m{f.metadata['attr']}\033[0m")
            print('\n'.join('    ' + line for line in wrap(f.metadata['help'])) + '\n')
        parser.exit()

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
