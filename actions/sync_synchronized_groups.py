# noinspection GrazieInspection
#
# IF YOU CHANGE THIS CODE OR DOCSTRING, PLEASE ALSO UPDATE THE USER
# DOCUMENTATION OF SYNCHRONIZED GROUPS LOCATED HERE:
# https://bookstack.icecube.wisc.edu/ops/books/keycloak-user-management/page/synchronized-groups
#
"""
Update membership of "synchronized" groups (i.e. groups managed by this script)
to be a subset of the union of their "source" groups. This action can implement
two membership control policies: "prune" and "match". Under the "prune" policy,
members who don't belong to any of the source groups are pruned. The "match"
policy prunes extraneous members and also adds missing members, thus making the
membership of the synchronized group match that of the union of the source groups.

This script has two modes of operation: "automatic" and "manual". In automatic
mode the script automatically discovers all "synchronized" groups configured
for automatic synchronization, loads their configuration from custom group
attributes and updates the groups' memberships according to the configured
policies. The manual mode is intended for debugging and silent initial population
of groups. In the manual mode, automatic discovery is disabled and some group
synchronization parameters can be overridden from the command line.

Two other important additional features of this script are grace period for
member removal and customizable notification.

Runtime configuration options are specified for each synchronized group as
custom group attributes. Use the command line flag --configuration-help
[link:ooK1Ua1B] to see all available configuration options. Note that user
notifications are enabled by default.

Paths of the source groups are specified as a JSONPath expression that yields
group paths when applied to the complete Keycloak group hierarchy (all groups
organized as a list of group trees, one tree per top-level group, with all
subGroups attributes populated recursively). The JSONPath expression uses the
extended syntax that is documented here: https://github.com/h2non/jsonpath-ng/.
There are some examples of typical JSONPaths patterns below.

This code was originally written to automate management of some /mail/subgroups
(mailing lists).

Custom Keycloak attributes used in this code are also documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes
Please update that page if you make changes to configuration options.

Examples::
    # Getting help on how to configure synchronized groups
    python -m actions.sync_synchronized_groups --configuration-help         # link:ooK1Ua1B

    # Simple JSONPath defining specific source groups by explicit path regular expression
    python -m actions.sync_synchronized_groups \
        --manual /path/to/group/composite-group \
            "$..subGroups[?path =~ '^/path/to/parent/((constituent-1)|(constituent-2))$'].path" \
        --dryrun                                                            # link:so5X1opu

    # JSONPath for all direct subgroups of certain parent groups,
    # in this case all institution groups of certain experiments.
    python -m actions.sync_synchronized_groups \
        --manual /path/to/group/composite-group \
            "$..subGroups[?path =~ '^/institutions/((ARA)|(CTA))$'].subGroups[*].path" \
        --dryrun                                                            # link:so5X1opu

    # More complex JSONPath defining source groups based on group
    # attribute values
    python -m actions.sync_synchronized_groups \
        --manual /mail/authorlist-test \
            "$..subGroups[?path == '/institutions/IceCube']
                .subGroups[?attributes.authorlist == 'true']
                    .subGroups[?name =~ '^authorlist.*'].path" \
        --dryrun                                                            # link:so5X1opu
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
from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timedelta
from enum import Enum
from itertools import chain
from jsonpath_ng.ext import parse  # type: ignore
from rest_tools.client import RestClient

from krs.email import send_email
from krs.groups import (get_group_membership, group_info, remove_user_group,
                        add_user_group, get_group_hierarchy, list_groups, modify_group)
from krs.token import get_rest_client
from krs.users import user_info

from actions.util import reflow_text


ACTION_ID = "sync_synchronized_groups"
logger = logging.getLogger(f'{ACTION_ID}')


@cached(Cache(maxsize=10000))
async def user_info_cached(username, keycloak):
    return await user_info(username, rest_client=keycloak)


@cached(Cache(maxsize=10000))
async def get_group_membership_cached(group_path, keycloak):
    return await get_group_membership(group_path, rest_client=keycloak)


@cached(Cache(maxsize=10000))
async def get_group_hierarchy_cached(keycloak):
    return await get_group_hierarchy(rest_client=keycloak)


class GrpCfgRes:
    """Group configuration resources. Hides stuff from the global structure
    view and autocomplete """
    # Prefix of custom group attribute names used for configuration
    ATTR_NAME_PREFIX = "synchronized_group_"
    MSG_HELP_FOOTER = ("Every @@ will be treated as a paragraph break and paragraphs will"
                       " be wrapped to look even-ish. Text can be a python f-string;"
                       " see --configuration-help for supported fields."  # link:ooK1Ua1B
                       " Standard footer will be appended. Default: empty string.")
    NOTIFICATION_APPEND_HELP = (f"Optional. Append this text to the default notification"
                                f" template for this event type. {MSG_HELP_FOOTER}")
    NOTIFICATION_OVERRIDE_HELP = (f'Optional. Use this template instead of the default one for'
                                  f' notifications of this event type. {MSG_HELP_FOOTER}')

    # Converter functions. Don't want to use lambdas since they
    # have no names, and we want to provide more meaningful messages
    # on conversion failures.
    @classmethod
    def double_at_to_newline(cls, s):
        return s.replace('@@', '\n\n')

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
class SyncGroupNotificationConfig:
    # Global force all notifications
    no_notifications: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="false",  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'no_notifications',
                        'help': 'Suppress all notifications. Overrides all other notification settings.'
                                ' Default: false.'}))

    # Event notification enable/disable options
    addition_occurred_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_notify',
                        'help': 'Send email notification when a user is added '
                                'to the group. Default: true.'}))
    removal_pending_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_notify',
                        'help': 'Send email notification when a user is scheduled '
                                'for removal (if grace period enabled). Default: true.'}))
    removal_averted_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_notify',
                        'help': 'Send email notification when a user is no longer scheduled '
                                'for removal (because they re-joined a source group before '
                                'the grace period expired). Default: true.'}))
    removal_occurred_notify: bool = (
        field(converter=GrpCfgRes.bool_from_string, default="true",  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_notify',
                        'help': 'Send email notification when a user is removed from the group '
                                'Default: true.'}))

    # Event notification message customizations
    addition_occurred_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_message_append',
                        'help': GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    addition_occurred_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'addition_occurred_message_override',
                        "help": GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_pending_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_pending_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_pending_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_averted_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_averted_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_averted_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))
    removal_occurred_message_append: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_message_append',
                        "help": GrpCfgRes.NOTIFICATION_APPEND_HELP}))
    removal_occurred_message_override: str = (
        field(converter=GrpCfgRes.double_at_to_newline, default='',  # keep default in sync with help
              metadata={'attr': GrpCfgRes.ATTR_NAME_PREFIX + 'removal_occurred_message_override',
                        'help': GrpCfgRes.NOTIFICATION_OVERRIDE_HELP}))


class MembershipSyncPolicy(Enum):
    """This script's membership control policies. See file docstring for details."""
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


class EmailTemplates(Enum):
    """Container for default message templates. Enum to make it easier
    to automatically generate documentation from it."""
    MESSAGE_FOOTER = f"""This message was generated by the {ACTION_ID} robot.
Please contact help@icecube.wisc.edu for support and feedback."""
    ADDITION_OCCURRED = """{username},\n
You have been automatically added to group {group_path} because you are a member of
group(s) {qualifying_groups}, and this requires you to also be in {group_path}."""
    REMOVAL_PENDING = """{username},\n
You have been scheduled for automatic removal from group {group_path} after {grace_days}
days because you are no longer a member in any of its prerequisite groups."""
    REMOVAL_AVERTED = """{username},\n
You are no longer scheduled for removal from group {group_path}."""
    REMOVAL_OCCURRED = """{username},\n
You have been automatically removed from group {group_path} because you are not
a member of any of its prerequisite groups."""


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
                [(fld.name, fld.metadata['attr']) for fld in missing_fields])

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
        """Configure synchronization settings of the group at group_path.

        Group attributes must be passed separately (and not be retrieved
        here from group_path) to allow higher layers to override settings.
        """
        # Set core parameters
        kwargs_super = {attr.name: group_attrs[attr.metadata['attr']]
                        for attr in SyncGroupCoreConfig.__attrs_attrs__
                        if attr.metadata['attr'] in group_attrs}
        self._validate_required_fields(SyncGroupCoreConfig, kwargs_super)
        self._validate_field_conversions(SyncGroupCoreConfig, kwargs_super)
        super().__init__(**kwargs_super)

        # Set notification parameters
        kwargs_notify = {attr.name: group_attrs[attr.metadata['attr']]
                         for attr in SyncGroupNotificationConfig.__attrs_attrs__
                         if attr.metadata['attr'] in group_attrs}
        self._validate_required_fields(SyncGroupNotificationConfig, kwargs_notify)
        self._validate_field_conversions(SyncGroupNotificationConfig, kwargs_notify)
        self._events = SyncGroupNotificationConfig(**kwargs_notify)

        # Set higher-level parameters
        self.group_path = group_path
        self.deferred_removals_attr = GrpCfgRes.ATTR_NAME_PREFIX + "deferred_removals"
        # noinspection PyTypeChecker
        self.sources_expr_str = group_attrs[fields(SyncGroupCoreConfig).sources_expr.metadata['attr']]

        # Cache deferred removals because they will be queried often.
        # Implement caching discipline ourselves because deferred removals
        # change during execution.
        self._deferred_removals_cache = None

        def construct_message(global_no_notify: bool, notify: bool, override: str, default: str,
                              append: str, footer: str) -> str:
            if global_no_notify or not notify:
                return ''
            else:
                # Note that the email text formatting code assumes paragraphs are separated
                # by \n\n. Things might look weird if there are extra newlines.
                return (override or (default + ("\n\n" + append if append else ''))) + "\n\n" + footer

        self.message_addition_occurred: str = construct_message(
            self._events.no_notifications, self._events.addition_occurred_notify,
            self._events.addition_occurred_message_override, EmailTemplates.ADDITION_OCCURRED.value,
            self._events.addition_occurred_message_append, EmailTemplates.MESSAGE_FOOTER.value)

        self.message_removal_pending: str = construct_message(
            self._events.no_notifications, self._events.removal_pending_notify,
            self._events.removal_pending_message_override, EmailTemplates.REMOVAL_PENDING.value,
            self._events.removal_pending_message_append, EmailTemplates.MESSAGE_FOOTER.value)

        self.message_removal_averted: str = construct_message(
            self._events.no_notifications, self._events.removal_averted_notify,
            self._events.removal_averted_message_override, EmailTemplates.REMOVAL_AVERTED.value,
            self._events.removal_averted_message_append, EmailTemplates.MESSAGE_FOOTER.value)

        self.message_removal_occurred: str = construct_message(
            self._events.no_notifications, self._events.removal_occurred_notify,
            self._events.removal_occurred_message_override, EmailTemplates.REMOVAL_OCCURRED.value,
            self._events.removal_occurred_message_append, EmailTemplates.MESSAGE_FOOTER.value)

    async def get_deferred_removals(self, keycloak: RestClient) -> dict:
        """Retrieve (cached) deferred removal state."""
        if self._deferred_removals_cache is None:
            group: dict = await group_info(self.group_path, rest_client=keycloak)
            group_attrs: dict = group.get('attributes', {})
            deferred_removals_raw: dict = json.loads(group_attrs.get(self.deferred_removals_attr, '{}'))
            self._deferred_removals_cache = dict((user, datetime.fromisoformat(ts))
                                                 for user, ts in deferred_removals_raw.items())
        return self._deferred_removals_cache

    async def set_deferred_removal(self, username: str, keycloak: RestClient):
        """Set deferred removal state of user to current time."""
        new_deferred_removal_str = datetime.now().isoformat()
        logger.info(f"Setting {username}'s removal timestamp to {new_deferred_removal_str}")
        deferred_removals = await self.get_deferred_removals(keycloak)
        deferred_removals[username] = new_deferred_removal_str
        deferred_removals_json = json.dumps(deferred_removals)
        self._deferred_removals_cache = None
        await modify_group(self.group_path, rest_client=keycloak,
                           attrs={self.deferred_removals_attr: deferred_removals_json})

    async def clear_deferred_removal(self, username: str, keycloak: RestClient):
        """Clear deferred removal info of user, if exists"""
        deferred_removals = await self.get_deferred_removals(keycloak)
        if deferred_removals.pop(username, None):
            deferred_removals_json = json.dumps(deferred_removals)
            self._deferred_removals_cache = None
            await modify_group(self.group_path, rest_client=keycloak,
                               attrs={self.deferred_removals_attr: deferred_removals_json})
            logger.info(f"Cleared deferred removal of {username}. New record: {deferred_removals}")


async def manual_group_sync(target_path: str,
                            source_groups_expr: str,
                            /, *,
                            keycloak_client: RestClient,
                            allow_notifications: bool,
                            dryrun: bool):
    """Execute a manual sync of members of the synchronized group at `target_path`.

    The configured source group expression will be overridden with `source_groups_expr`.
    Notifications may be forced disabled with `allow_notifications`.

    Args:
        target_path (str): path to the target synchronized group
        source_groups_expr (str): JSONPath expression that yields constituent group paths
                                  when applied to the complete Keycloak group hierarchy.
        keycloak_client (RestClient): REST client to the KeyCloak server
        allow_notifications (bool): if False, suppress email notifications
        dryrun (bool): perform a trial run with no changes made
    """
    logger.info(f"Manually syncing {target_path}")
    target_group = await group_info(target_path, rest_client=keycloak_client)
    target_group_attrs = target_group.get('attributes', {})

    # noinspection PyTypeChecker
    source_groups_expr_attr = fields(SyncGroupConfig).sources_expr.metadata['attr']
    if source_groups_expr:
        # override sources expression
        target_group_attrs[source_groups_expr_attr] = source_groups_expr
    logger.info(f"Constituents expression: {source_groups_expr or target_group_attrs[source_groups_expr_attr]}")

    try:
        cfg = SyncGroupConfig(target_path, target_group_attrs)
    except (SyncGroupConfigAttributeError, SyncGroupConfigValueError) as exc:
        logger.error(f"{target_path} configuration exception {exc!r}")
        return 1

    if cfg.auto_sync:
        # noinspection PyTypeChecker
        logger.critical(f"To operate in manual mode on {target_path}, its "
                        f"{fields(SyncGroupConfig).auto_sync.metadata['attr']} attribute must not be true.")
        return 1

    return await sync_synchronized_group(target_path,
                                         cfg=cfg,
                                         keycloak=keycloak_client,
                                         allow_notifications=allow_notifications,
                                         dryrun=dryrun)


async def auto_sync_enabled_groups(keycloak_client, dryrun):
    """Discover enabled synchronized groups and sync them.

    Args:
        keycloak_client (RestClient): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Find all enabled synchronized groups. At the moment, it's much faster
    # to list all groups and pick the ones we need in python, compared to
    # querying custom attributes via REST API.
    all_groups = await list_groups(rest_client=keycloak_client)
    # noinspection PyTypeChecker
    auto_sync_attr = fields(SyncGroupConfig).auto_sync.metadata['attr']
    enabled_group_paths = [group['path'] for group in all_groups.values()
                           if group.get('attributes', {})
                           .get(auto_sync_attr, '').lower() == "true"]

    for enabled_group_path in enabled_group_paths:
        enabled_group = await group_info(enabled_group_path, rest_client=keycloak_client)
        try:
            cfg = SyncGroupConfig(enabled_group_path, enabled_group['attributes'])
        except (SyncGroupConfigAttributeError, SyncGroupConfigValueError) as exc:
            logger.error(f"{enabled_group_path} sync configuration exception {exc!r}")
            raise

        try:
            await sync_synchronized_group(enabled_group_path,
                                          cfg=cfg,
                                          keycloak=keycloak_client,
                                          allow_notifications=True,
                                          dryrun=dryrun)
        except Exception as exc:
            logger.error(f"Exception during sync of {enabled_group_path}: {exc!r}")
            raise


async def send_notification(username: str, subject: str, body: str, keycloak: RestClient):
    user = await user_info_cached(username, keycloak)
    user_attrs = user['attributes']

    # In general, we don't know what email the user checks,
    # so send to all emails we know of.
    to_address = f"{username}@icecube.wisc.edu"
    cc_addresses = list(filter(None, {user.get('email'), user_attrs.get('mailing_list_email')}))

    # Remove duplicate addresses if exist (sometimes users set
    # their email and mailing_list_email to icecube addresses)
    with suppress(ValueError):
        cc_addresses.remove(to_address)
    with suppress(ValueError):
        cc_addresses.remove(user_attrs.get('canonical_email'))

    logger.info(f"Sending '{subject}' notification to={to_address}, cc={cc_addresses}")
    send_email(to_address, subject, reflow_text(body, break_on_hyphens=False),
               cc=cc_addresses, headline="IceCube Automatic Group Management")


async def clear_deferred_removal(username: str, cfg: SyncGroupConfig, dryrun: bool,
                                 notify: bool, keycloak: RestClient):
    """Remove a user from the deferred removal records """
    deferred_removals: dict = await cfg.get_deferred_removals(keycloak)
    if deferred_removals.get(username):
        logger.info(f"Removing {username} from deferred removal state({dryrun=}, {notify=})")
        if not dryrun:
            await cfg.clear_deferred_removal(username, keycloak)
            if notify and cfg.message_removal_averted:
                await send_notification(
                    username=username, keycloak=keycloak,
                    subject=f"You are no longer scheduled for removal from group {cfg.group_path}",
                    body=cfg.message_removal_averted.format(username=username, group_path=cfg.group_path))


async def grace_period_check_with_init(username: str, cfg: SyncGroupConfig, dryrun: bool,
                                       notify: bool, keycloak: RestClient) -> bool:
    """Set and/or check whether the user passes grace period check

    Assumes removal grace period is enabled and non-zero.
    Sets deferred removal state if missing.

    Return:
        (bool) whether the user's removal grace period has expired
    """
    if not cfg.removal_grace_days:
        return False  # grace=0, so it expires immediately and everybody fails the check

    deferred_removals = await cfg.get_deferred_removals(keycloak)

    if removal_scheduled_at := deferred_removals.get(username):
        if datetime.now() < removal_scheduled_at + timedelta(days=cfg.removal_grace_days):
            return True  # grace not expired, check passed
        else:
            logger.info(f"Removal grace period of {username} expired ({removal_scheduled_at,cfg.removal_grace_days=})")
            return False  # grace expired, check failed
    else:
        # Grace period > 0 but "removal scheduled" not set. Set it.
        if not dryrun:
            await cfg.set_deferred_removal(username, keycloak)
            if notify and cfg.message_removal_pending:
                await send_notification(
                    username=username, keycloak=keycloak,
                    subject=f"You are scheduled for removal from group {cfg.group_path}",
                    body=cfg.message_removal_pending.format(username=username, group_path=cfg.group_path,
                                                            grace_days=cfg.removal_grace_days))
        # Assuming grace=0 case has been handled earlier
        return True  # pass the check since grace>0 and grace period has just been begun


async def remove_extraneous_member(username: str, cfg: SyncGroupConfig, dryrun: bool, notify: bool,
                                   keycloak: RestClient):
    """Removes an extraneous member"""
    if username in await cfg.get_deferred_removals(keycloak):
        logger.info(f"Removing {username} from deferred removal state ({dryrun=}, {notify=})")
        if not dryrun:
            await cfg.clear_deferred_removal(username, keycloak)
    logger.info(f"Removing extraneous {username} from {cfg.group_path} ({dryrun=}, {notify=}")
    if not dryrun:
        await remove_user_group(cfg.group_path, username, rest_client=keycloak)
        if notify and cfg.message_removal_occurred:
            await send_notification(
                username=username, keycloak=keycloak,
                subject=f"You have been removed from group {cfg.group_path}",
                body=cfg.message_removal_occurred.format(username=username, group_path=cfg.group_path))


async def add_missing_member(username: str, qualifying_groups: list, cfg: SyncGroupConfig,
                             dryrun: bool, notify: bool, keycloak: RestClient):
    """Add a user who should be group members but isn't."""
    logger.info(f"Adding {username} to {cfg.group_path} ({dryrun=}, {notify=})")
    if dryrun:
        return
    await add_user_group(cfg.group_path, username, rest_client=keycloak)
    if notify and cfg.message_addition_occurred:
        await send_notification(
            username=username, keycloak=keycloak,
            subject=f"You have been added to group {cfg.group_path}",
            body=cfg.message_addition_occurred.format(
                username=username, group_path=cfg.group_path,
                qualifying_groups=', '.join(qualifying_groups)))


async def sync_synchronized_group(target_path: str,
                                  /, *,
                                  cfg: SyncGroupConfig,
                                  keycloak: RestClient,
                                  allow_notifications: bool,
                                  dryrun: bool):
    """Synchronize membership of the synchronized group at `target_path`.

    `constituents_expr` is a string with JSONPath expression that will be
    applied to the complete group hierarchy to extract paths of the source
    groups.

    Although runtime configuration options are stored as the target group's
    custom attributes, this code shall not access them directly, and instead
    use the `cfg` parameter. This is to allow some options to be overridden.

    This function caches some calls to Keycloak. It's possible inter-depended
    synchronized groups will be processed during the same run and caching will
    hide group changes made by this script. This is OK since this will be rare
    and membership updates will eventually propagate on a later run.

    Args:
        target_path (str): path to the target synchronized group
        cfg (SyncGroupConfig): runtime configuration options
        keycloak (RestClient): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        allow_notifications (bool): if False, suppress all email notifications
    """
    # Set up partials to make the code easier to read
    logger.debug(f"Processing synchronized group {target_path}")

    # noinspection PyCallingNonCallable
    group_hierarchy = await get_group_hierarchy_cached(keycloak)
    constituent_group_paths = [v.value for v in cfg.sources_expr.find(group_hierarchy)]
    logger.debug(f"{sorted(constituent_group_paths)=}")

    # Sanity check source group paths. It's easy to make a mistake in the JSONPath
    # expression that would cause it to produce garbage
    group_path_type_error = group_path_value_error = None
    if not all(isinstance(path, str) for path in constituent_group_paths):
        group_path_type_error = True
    # Check for valid group paths. Note that Keycloak is actually more liberal
    # When it comes to group names, but IceCube policy (at least right now) is
    # letters, numbers, -, and _. No spaces.
    elif not all(re.match(f'(/[-_{string.ascii_letters}{string.digits}]+)+$', path)
                 for path in constituent_group_paths):
        group_path_value_error = True
    if group_path_type_error or group_path_value_error:
        logger.error("Results of sources expression don't look like group paths:")
        logger.error(f"{cfg.sources_expr_str=}")
        logger.error(f"{str(constituent_group_paths)[:200]=}")
        if group_path_type_error:
            raise TypeError("Source paths expression produced non-string objects")
        if group_path_value_error:
            raise ValueError("Source paths expression produced invalid paths")

    # Determine what the current membership and memberships of the source groups
    constituent_member_lists = await asyncio.gather(
        *[get_group_membership_cached(group_path, keycloak)
          for group_path in constituent_group_paths])
    source_groups_member_dict = dict(zip(constituent_group_paths, constituent_member_lists))
    source_members = set(chain.from_iterable(constituent_member_lists))
    current_members = set(await get_group_membership(target_path, rest_client=keycloak))
    logger.debug(f"{sorted(source_members)=}")

    user_memberships = defaultdict(list)
    for group, members in source_groups_member_dict.items():
        for username in members:
            user_memberships[username].append(group)

    # Process the current legitimate members that don't need to be removed
    for valid_member in current_members & source_members:
        # Valid users may need to be removed from the deferred removal record
        # if they rejoined a constituent group before the grace period expired
        if valid_member in await cfg.get_deferred_removals(keycloak):
            await clear_deferred_removal(valid_member, cfg, dryrun, allow_notifications, keycloak)

    # Prune extraneous members
    for extraneous_member in current_members - source_members:
        if cfg.removal_grace_days:
            if await grace_period_check_with_init(extraneous_member, cfg, dryrun, allow_notifications, keycloak):
                continue
        await remove_extraneous_member(extraneous_member, cfg, dryrun, allow_notifications, keycloak)

    # Add missing members if policy is to match union of membership of constituents
    if cfg.policy == MembershipSyncPolicy.match:
        for missing_member in source_members - current_members:
            await add_missing_member(missing_member, user_memberships[missing_member],
                                     cfg, dryrun, allow_notifications, keycloak)


def print_configuration_help():  # link:ooK1Ua1B
    from textwrap import wrap
    print("\n\033[4;7m" + "Core configuration attributes:".upper() + "\033[0m\n")
    # noinspection PyTypeChecker
    for f in fields(SyncGroupCoreConfig):
        print(f"\033[3m{f.metadata['attr']}\033[0m")
        print('\n'.join('    ' + line for line in wrap(f.metadata['help'])) + '\n')

    print("\n\033[4;7m" + "Attributes configuring notifications:".upper() + "\033[0m\n")
    # noinspection PyTypeChecker
    for f in fields(SyncGroupNotificationConfig):
        print(f"\033[3m{f.metadata['attr']}\033[0m")
        print('\n'.join('    ' + line for line in wrap(f.metadata['help'])) + '\n')

    print("\n\033[4;7m" + "Default notification templates:".upper() + "\033[0m\n")
    for msg in EmailTemplates:
        print(f"\033[3m{msg.name}\033[0m")
        print('\n'.join('    ' + line for line in reflow_text(msg.value).split('\n')) + '\n')


async def display_notifications(target_path, keycloak):
    target_group = await group_info(target_path, rest_client=keycloak)
    target_group_attrs = target_group.get('attributes', {})

    try:
        cfg = SyncGroupConfig(target_path, target_group_attrs)
    except (SyncGroupConfigAttributeError, SyncGroupConfigValueError) as exc:
        logger.error(f"{target_path} configuration exception {exc!r}")
        return

    no_notification = "<notifications disabled for this event>"
    print("\n\033[4;7m" + "Addition occurred:".upper() + "\033[0m")
    print(reflow_text(cfg.message_addition_occurred) or no_notification, '\n')
    print("\n\033[4;7m" + "Removal pending:".upper() + "\033[0m")
    print(reflow_text(cfg.message_removal_pending) or no_notification, '\n')
    print("\n\033[4;7m" + "Removal averted:".upper() + "\033[0m")
    print(reflow_text(cfg.message_removal_averted) or no_notification, '\n')
    print("\n\033[4;7m" + "Removal occurred:".upper() + "\033[0m")
    print(reflow_text(cfg.message_removal_occurred) or no_notification, '\n')


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync membership of synchronized group(s) with their corresponding '
                    'source groups. See file docstring for details and examples.',
        epilog="*** SEE FILE DOCSTRING FOR DETAILS AND EXAMPLES ***",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument('--configuration-help', action='store_true',  # link:ooK1Ua1B
                       help="Display help on synchronized groups' configuration attributes and exit.")
    mutex.add_argument('--display-notifications', metavar='TARGET_GROUP_PATH',
                       help="Display all notification TARGET_GROUP_PATH is configured to send and exit.")
    mutex.add_argument('--auto', action='store_true',
                       help='Automatically discover all enabled synchronized groups and sync them.')
    mutex.add_argument('--manual', nargs=2, metavar=('TARGET_GROUP_PATH', 'JSONPATH_EXPR|""'),  # link:so5X1opu
                       help="Sync the synchronized group at TARGET_GROUP_PATH with the "
                            "source groups at paths defined by JSONPATH_EXPR. If JSONPATH_EXPR "
                            "is empty, use the expression from the group's configuration.")
    parser.add_argument('--allow-notifications', action='store_true',
                        help="Do send out email notifications if so configured. Required in automatic mode.")
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'),
                        help='Root logging level.')
    parser.add_argument('--log-level-this', default='info', choices=('debug', 'info', 'warning', 'error'),
                        help='Logging level of this application (not dependencies).')
    parser.add_argument('--log-level-client', default='warning', choices=('debug', 'info', 'warning', 'error'),
                        help='REST client logging level.')
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    args = vars(parser.parse_args())

    if args['configuration_help']:   # link:ooK1Ua1B
        print_configuration_help()
        parser.exit()

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))
    cca_logger = logging.getLogger('ClientCredentialsAuth')
    cca_logger.setLevel(getattr(logging, args['log_level_client'].upper()))
    this_logger = logging.getLogger(ACTION_ID)
    this_logger.setLevel(getattr(logging, args['log_level_this'].upper()))

    if not args['allow_notifications'] and args['auto']:
        logger.critical("--allow-notifications is required in automatic mode")
        parser.exit(1)

    keycloak_client = get_rest_client()

    if args['display_notifications']:
        asyncio.run(display_notifications(args['display_notifications'], keycloak_client))
        parser.exit()

    if args['auto']:
        return asyncio.run(auto_sync_enabled_groups(
            keycloak_client=keycloak_client,
            dryrun=args['dryrun']))
    else:
        target_group, source_group_expr = args['manual']
        return asyncio.run(manual_group_sync(target_group,
                                             source_group_expr,
                                             keycloak_client=keycloak_client,
                                             allow_notifications=args['allow_notifications'],
                                             dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
