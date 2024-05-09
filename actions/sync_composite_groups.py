"""
Sync membership of the target composite group(s) to match the union of
the memberships of their constituent source groups.

Paths of the constituent groups are specified as a JSONPath expression
to be applied to the complete Keycloak group hierarchy (list of group
trees, one per top-level group, containing all groups). The JSONPath
expression uses the extended syntax that is documented here:
https://github.com/h2non/jsonpath-ng/.

Two important features of this action are support for removals deferred
by a grace period and email notifications.

Runtime configuration options are specified for each composite group as
custom group attributes. See documentation of the `sync_composite_groups_*`
attributes for the available configuration options (link to documentation
below). Note that the required attributes are:
 * sync_composite_groups_enable
 * sync_composite_groups_constituents_expr

The target composite group(s) and the JSONPath specifications of their
constituents are either provided on the command line (manual mode) or
discovered automatically (automatic mode).

Manual mode is intended mostly for testing and debugging (e.g. of JSONPath
expressions), but could also be useful for initial silent seeding of composite
groups. To run this code in manual mode, in order to minimize chances of
collisions, the target composite group's attribute `sync_composite_groups_enable`
must be empty or absent, and the `sync_composite_groups_constituents_expr`
attribute must be empty, or absent, or be the same as the expression given
on the command line.

Originally written to automate management of some /mail/ subgroups
(mailing lists).

Custom Keycloak attributes used in this code are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.sync_composite_groups \
        --target-spec /mail/authorlist-test \
            '$..subGroups[?path == "/institutions/IceCube"]
                .subGroups[?attributes.authorlist == "true"]
                    .subGroups[?name =~ "^authorlist.*"].path' \
        --dryrun
"""

import asyncio
import logging
import sys
from attrs import *
from datetime import datetime, timedelta
from functools import partial
from itertools import chain
from jsonpath_ng.ext import parse  # type: ignore
from rest_tools.client.client_credentials import ClientCredentialsAuth

from krs.email import send_email
from krs.groups import (get_group_membership, group_info, remove_user_group,
                        add_user_group, get_group_hierarchy, list_groups)
from krs.token import get_rest_client
from krs.users import user_info, modify_user

ATTR_NAME_PREFIX = "sync_composite_groups_"

@define
class _Config:
    XXXfoo = lambda s: s.replace('@@', '\n') if s else None
    group_path: str = field()
    mode: str = field(validator=validators.in_(('off', 'filter', 'match')),
                      metadata={'attr': ATTR_NAME_PREFIX + 'mode'})
    XXXremoval_scheduled_at_user_attr_name: str = field()
    removal_pending_notify: bool = field()
    removal_averted_notify: bool = field()
    removal_occurred_notify: bool = field()
    sources_expr = field(converter=lambda x: parse(x) if x else None, default=None,
                         metadata={'attr': ATTR_NAME_PREFIX + 'sources_expr'})
    removal_grace_days: int = (
        field(converter=lambda x: int(x) if x else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_grace_days'}))
    removal_pending_message_append: str = (
        field(converter=lambda s: s.replace('@@', '\n') if s else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_pending_message_append'}))
    removal_pending_message_override: str = (
        field(converter=lambda s: s.replace('@@', '\n') if s else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_pending_message_override'}))
    removal_averted_message_append: str = (
        field(converter=lambda s: s.replace('@@', '\n') if s else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_averted_message_append'}))
    removal_averted_message_override: str = (
        field(converter=lambda s: s.replace('@@', '\n') if s else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_averted_message_override'}))
    removal_occurred_message_append: str = (
        field(converter=lambda s: s.replace('@@', '\n') if s else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_occurred_message_append'}))
    removal_occurred_message_override: str = (
        field(converter=lambda s: s.replace('@@', '\n') if s else None, default=None,
              metadata={'attr': ATTR_NAME_PREFIX + 'removal_occurred_message_override'}))

class Config(_Config):
    def __init__(self, group_path, group_attrs):
        kwargs = {a.name: group_attrs[a.metadata['attr']]
                  for a in _Config.__attrs_attrs__
                  if a.metadata['attr'] in group_attrs}
        kwargs['removal_scheduled_user_attr_name'] = f"{group_path}_removal_scheduled_at"

        super().__init__(**kwargs)


logger = logging.getLogger('sync_composite_groups')

MESSAGE_TEMPLATE_FOOTER = """
This message was generated by the sync_composite_groups robot.
Please contact help@icecube.wisc.edu for support.
"""

REMOVAL_AVERTED_TEMPLATE = """
{username},

You are no longer scheduled for removal from group {group_path}.

{custom_text}

""" + MESSAGE_TEMPLATE_FOOTER

REMOVAL_PENDING_TEMPLATE = """
{username},

You have been scheduled for removal from group {group_path}
because you are not a member of any of its constituent groups.
Unless you (re)join one of those groups, you will be removed
after a grace period.

{custom_text}

""" + MESSAGE_TEMPLATE_FOOTER

REMOVAL_OCCURRED_TEMPLATE = """
{username},

You have been removed from group {group_path}
because you are not a member of any of its constituent groups.

{custom_text}

""" + MESSAGE_TEMPLATE_FOOTER

WELCOME_TEMPLATE = """
{username},

You have been added to group {group_path} because you
are a member of one of its constituent groups.

{custom_text}

""" + MESSAGE_TEMPLATE_FOOTER


async def manual_sync(target_path: str,
                      constituents_expr: str,
                      /, *,
                      keycloak_client: ClientCredentialsAuth,
                      notify: bool = False,
                      dryrun: bool = False):
    """Execute a manual sync (add/remove) of members of the composite group
    at `target_path` to the union of the memberships of constituent groups
    specified by `constituents_expr`.

    See docstring of sync_composite_group(), argparse help, and this file's
    docstring for more details.

    Args:
        target_path (str): path to the destination composite group
        constituents_expr (str): JSONPath expression that yields constituent group paths
                                 when applied to the complete Keycloak group hierarchy.
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        notify (bool): send email notifications
    """
    logger.info(f"Manually syncing {target_path}")
    logger.info(f"Constituents expression: {constituents_expr}")
    target_group = await group_info(target_path, rest_client=keycloak_client)

    cfg = Config(target_group['attributes'])
    if cfg.mode != 'off':
        # noinspection PyTypeChecker
        logger.critical(f"To operate in manual mode, {target_path}'s "
                        f"{fields(Config).mode.metadata['attr']} attribute must be empty or absent")
        return 1

    # override sources expr
    cfg.sources_expr = constituents_expr

    return await sync_composite_group(target_path,
                                      cfg=cfg,
                                      keycloak_client=keycloak_client,
                                      notify=notify,
                                      dryrun=dryrun)


async def auto_sync(keycloak_client, dryrun):
    """Discover enabled composite groups and sync them.

    See docstring of sync_composite_group(), argparse help, and this file's
    docstring for more details.

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
                           .get(fields(Config).mode.metadata['attr']) in ('filter', 'match')]

    for enabled_group_path in enabled_group_paths:
        enabled_group = await group_info(enabled_group_path, rest_client=keycloak_client)
        cfg = Config(enabled_group['attributes'])
        await sync_composite_group(enabled_group_path,
                                   cfg=cfg,
                                   keycloak_client=keycloak_client,
                                   notify=True,
                                   dryrun=dryrun)


async def sync_composite_group(target_path: str,
                               /, *,
                               cfg: Config,
                               keycloak_client: ClientCredentialsAuth,
                               notify: bool,
                               dryrun: bool = False):
    """Synchronize (add/remove) membership of the composite group at
    `target_path` to the union of the memberships of constituent groups
    specified by `constituents_expr`.

    `constituents_expr` is a string with JSONPath expression that will be
    applied to the complete group hierarchy to extract paths of the constituent
    groups.

    Although runtime configuration options are stored as the target group's
    custom attributes, this code shall not access them directly, and instead
    use the `opts` parameter. This is to allow some options to be overridden.

    The runtime configuration options are documented here:
    https://bookstack.icecube.wisc.edu/ops/books/keycloak-user-management/page/custom-keycloak-attributes

    See docstring of sync_composite_group(), argparse help, and this file's
    docstring for more details.

    Args:
        target_path (str): path to the destination composite group
        constituents_expr (str): JSONPath expression that yields constituent group paths
                                 when applied to the complete Keycloak group hierarchy.
        opts (dict): dictionary with runtime configuration options
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        notify (bool): send email notifications
    """
    # Set up partials to make the code easier to read
    _add_user_group = partial(add_user_group, rest_client=keycloak_client)
    _get_group_hierarchy = partial(get_group_hierarchy, rest_client=keycloak_client)
    _get_group_membership = partial(get_group_membership, rest_client=keycloak_client)
    _modify_user = partial(modify_user, rest_client=keycloak_client)
    _remove_user_group = partial(remove_user_group, rest_client=keycloak_client)
    _user_info = partial(user_info, rest_client=keycloak_client)

    logger.info(f"Processing composite group {target_path}")

    # Build the list of all constituent groups' paths
    group_hierarchy = await _get_group_hierarchy()
    source_group_paths = [v.value for v in cfg.sources_expr.find(group_hierarchy)]
    logger.debug(f"Syncing {target_path} to {source_group_paths}")

    # Determine what the current membership is and what it should be
    intended_members_lists = [await _get_group_membership(source_group_path)
                              for source_group_path in source_group_paths]
    intended_members = set(chain.from_iterable(intended_members_lists))
    current_members = set(await _get_group_membership(target_path))

    # Reset removal grace times of intended current members (will be set if
    # they rejoined a constituent group before removal grace period expired)
    for valid_member in current_members & intended_members:
        user = await _user_info(valid_member)
        attrs = user['attributes']
        if attrs.get(cfg.removal_scheduled_user_attr_name):
            logger.info(f"Clearing {valid_member}'s {cfg.removal_scheduled_user_attr_name} ({dryrun,notify=})")
            if dryrun:
                continue
            await _modify_user(valid_member, attribs={cfg.removal_scheduled_user_attr_name: None})
            if not notify or not cfg.removal_averted_message:
                logger.info(f"Skipping notification ({notify,removal_averted_message=})")
                continue
            address = notification_redirect_addr or f"{valid_member}@icecube.wisc.edu"
            logger.info(f"Sending 'removal averted' notification to {address} ({dryrun,notify=})")
            # noinspection PyTypeChecker
            send_email(address, f"You are no longer scheduled for removal from group {target_path}",
                       REMOVAL_AVERTED_TEMPLATE.format(
                           username=current_members,
                           group_path=target_path,
                           custom_text=removal_averted_message),
                       cc=notification_email_cc)

    # Process the current members that don't belong to any constituent group,
    # removing them if grace period is undefined or expired
    for extraneous_member in current_members - intended_members:
        logger.info(f"{extraneous_member} shouldn't be in {target_path} ({dryrun,notify=})")
        if dryrun:
            continue
        user = await _user_info(extraneous_member)
        attrs = user['attributes']

        if removal_grace_days:
            if removal_scheduled_at_str := attrs.get(removal_scheduled_user_attr_name):
                removal_scheduled_at = datetime.fromisoformat(removal_scheduled_at_str)
                # move on if too early to remove
                if datetime.now() < removal_scheduled_at + timedelta(days=removal_grace_days):
                    logger.info(f"Too early to remove {extraneous_member} {removal_scheduled_at_str=}")
                    continue
                else:
                    logger.info(f"Removal grace period expired ({removal_scheduled_at_str,removal_grace_days=})")
            else:
                # "Removal scheduled attribute" attribute not set. Set it and move on.
                new_removal_scheduled_at_str = datetime.now().isoformat()
                logger.info(f"Setting {extraneous_member}'s {removal_scheduled_user_attr_name} "
                            f"to {new_removal_scheduled_at_str} ({dryrun,notify=})")
                await _modify_user(extraneous_member,
                                   attribs={removal_scheduled_user_attr_name:
                                            new_removal_scheduled_at_str})
                if not notify or not removal_pending_message:
                    logger.info(f"Skipping notification ({notify,removal_pending_message=})")
                    continue
                address = notification_redirect_addr or f"{extraneous_member}@icecube.wisc.edu"
                logger.info(f"Sending 'scheduled for removal' notification to {address} ({dryrun,notify=})")
                # noinspection PyTypeChecker
                send_email(address, f"You are scheduled for removal from group {target_path}",
                           REMOVAL_PENDING_TEMPLATE.format(
                               username=extraneous_member,
                               group_path=target_path,
                               custom_text=removal_pending_message),
                           cc=notification_email_cc)
                continue
        # Either grace period not configured or grace period expired.
        # Remove the user from the group.
        logger.info(f"Clearing {extraneous_member}'s {removal_scheduled_user_attr_name} attribute ({dryrun,notify=})")
        await _modify_user(extraneous_member, attribs={removal_scheduled_user_attr_name: None})
        logger.info(f"Removing {extraneous_member} from {target_path} ({dryrun,notify=}")
        await _remove_user_group(target_path, extraneous_member)
        if not notify or not removal_occurred_message:
            logger.info(f"Skipping notification ({notify,removal_occurred_message=})")
            continue
        address = notification_redirect_addr or f"{extraneous_member}@icecube.wisc.edu"
        logger.info(f"Sending 'removal occurred' notification to {address} ({dryrun,notify=})")
        # noinspection PyTypeChecker
        send_email(address, f"You have been removed from group {target_path}",
                   REMOVAL_OCCURRED_TEMPLATE.format(
                       username=extraneous_member,
                       group_path=target_path,
                       custom_text=removal_occurred_message),
                   cc=notification_email_cc)

    # Add missing members to the group
    for missing_member in intended_members - current_members:
        logger.info(f"adding {missing_member} to {target_path} ({dryrun,notify=})")
        if dryrun:
            continue
        await _add_user_group(target_path, missing_member)
        if not notify or not welcome_message:
            continue
        address = notification_redirect_addr or f"{missing_member}@icecube.wisc.edu"
        logger.info(f"Sending 'added to group' notification to {address} ({dryrun,notify=})")
        # noinspection PyTypeChecker
        send_email(address, f"You have been added to group {target_path}",
                   WELCOME_TEMPLATE.format(
                       username=missing_member,
                       group_path=target_path,
                       custom_text=welcome_message),
                   cc=notification_email_cc)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync membership of the composite group(s) to match the union of the '
                    'memberships of their constituent source groups. The constituent group '
                    'paths are specified as a JSONPath expression to be applied to the complete '
                    'Keycloak group hierarchy. '
                    'See Epilog for additional information. '
                    'See file docstring for details and examples. ',
        epilog="This code uses the extended JSONPath parser from the `jsonpath_ng` module. "
               "For syntax and a quickstart, see https://github.com/h2non/jsonpath-ng/. "
               "Custom Keycloak attributes used by this code are documented here: "
               "https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes. "
               "See file docstring for more details and examples. ",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument('--auto', action='store_true',
                       help='automatically discover all enabled composite groups and sync '
                            'them using configuration stored in their attributes. '
                            'See file docstring for details')
    mutex.add_argument('--manual', nargs=2, metavar=('TARGET_GROUP_PATH', 'JSONPATH_EXPR'),
                       help="sync the composite group at TARGET_GROUP_PATH with the constituent "
                            "groups produced by JSONPATH_EXPR when applied to the complete "
                            "Keycloak group hierarchy. "
                            "Hints: "
                            "(1) See epilog for more information. "
                            "(2) See file docstring for a good example of a non-trivial "
                            "JSONPath expression.")
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    parser.add_argument('--notify', action='store_true',
                        help="send email notifications if using --manual; required with --auto")
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))
    if args['log_level'] == 'info':
        # ClientCredentialsAuth is too verbose at INFO
        cca_logger = logging.getLogger('ClientCredentialsAuth')
        cca_logger.setLevel('WARNING')

    if not args['notify'] and args['auto']:
        logger.critical("--notify is required with --auto")
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
                                       notify=args['notify'],
                                       dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
