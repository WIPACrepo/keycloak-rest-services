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


logger = logging.getLogger('sync_composite_groups')

# Attribute names of runtime configuration options
IS_ENABLED_ATTR = "sync_composite_groups_enable"
CONSTITUENTS_EXPR_ATTR = "sync_composite_groups_constituents_expr"
NOTIFICATION_CC_ATTR = 'sync_composite_groups_notification_email_cc'
NOTIFICATION_REDIRECT_ADDR_ATTR = 'sync_composite_groups_notification_redirect'
WELCOME_MSG_ATTR = 'sync_composite_groups_member_welcome_message'
REMOVAL_GRACE_DAYS_ATTR = 'sync_composite_groups_member_removal_grace_days'
REMOVAL_PENDING_MSG_ATTR = 'sync_composite_groups_member_removal_pending_message'
REMOVAL_AVERTED_MSG_ATTR = 'sync_composite_groups_member_removal_averted_message'
REMOVAL_OCCURRED_MSG_ATTR = 'sync_composite_groups_member_removal_occurred_message'

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
Unless you (re)join one of those groups, you will be removed from
{group_path} after a grace period.

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

You have been added to group {group_path}.

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
    attrs = target_group['attributes']
    if attrs.get(IS_ENABLED_ATTR):
        logger.critical(f"To operate in manual mode, {target_path}'s "
                        f"{IS_ENABLED_ATTR} attribute must be empty or absent")
        return 1
    if group_constituents_expr := attrs.get(CONSTITUENTS_EXPR_ATTR):
        if group_constituents_expr != constituents_expr:
            logger.critical(f"To operate in manual mode, {target_path}'s "
                            f"{CONSTITUENTS_EXPR_ATTR} attribute must be empty, absent, "
                            f"or equal to the expression given on the command line")
            logger.critical(f"command line: {attrs[CONSTITUENTS_EXPR_ATTR]}")
            logger.critical(f"{CONSTITUENTS_EXPR_ATTR}: {attrs[CONSTITUENTS_EXPR_ATTR]}")
            return 1

    # set expr in case it's empty
    attrs['sync_composite_groups_constituents_expr'] = constituents_expr

    return await sync_composite_group(target_path,
                                      constituents_expr,
                                      opts=attrs,
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
    enabled_group_paths = [v['path'] for v in all_groups.values()
                           if v.get('attributes', {}).get(IS_ENABLED_ATTR) == 'true']

    for enabled_group_path in enabled_group_paths:
        enabled_group = await group_info(enabled_group_path, rest_client=keycloak_client)
        attrs = enabled_group['attributes']
        await sync_composite_group(enabled_group_path,
                                   attrs[CONSTITUENTS_EXPR_ATTR],
                                   opts=attrs,
                                   keycloak_client=keycloak_client,
                                   notify=True,
                                   dryrun=dryrun)


async def sync_composite_group(target_path: str,
                               constituents_expr: str,
                               /, *,
                               opts: dict,
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
    group_hierarchy = _get_group_hierarchy()
    parsed_expr = parse(constituents_expr)
    source_group_paths = [v.value for v in parsed_expr.find(group_hierarchy)]
    logger.debug(f"Syncing {target_path} to {source_group_paths}")

    # Determine what the current membership is and what it should be
    intended_members_lists = [await _get_group_membership(source_group_path)
                              for source_group_path in source_group_paths]
    intended_members = set(chain.from_iterable(intended_members_lists))
    current_members = set(await _get_group_membership(target_path))

    # Get all config values into own variables to make code easier to read
    removal_scheduled_user_attr_name = f"{target_path}_removal_scheduled_at"
    removal_grace_days = opts.get(REMOVAL_GRACE_DAYS_ATTR)
    removal_pending_message = opts.get(REMOVAL_PENDING_MSG_ATTR, '').replace('@@', '\n')
    removal_averted_message = opts.get(REMOVAL_AVERTED_MSG_ATTR, '').replace('@@', '\n')
    removal_occurred_message = opts.get(REMOVAL_OCCURRED_MSG_ATTR, '').replace('@@', '\n')
    welcome_message = opts.get(WELCOME_MSG_ATTR, '').replace('@@', '\n')
    notification_email_cc = opts.get(NOTIFICATION_CC_ATTR)
    notification_redirect_addr = opts.get(NOTIFICATION_REDIRECT_ADDR_ATTR)

    # Reset removal grace times of intended current members (will be set if
    # they rejoined a constituent group before removal grace period expired)
    for valid_member in current_members & intended_members:
        user = await _user_info(valid_member)
        attrs = user['attributes']
        if attrs.get(removal_scheduled_user_attr_name):
            logger.info(f"Clearing {valid_member}'s {removal_scheduled_user_attr_name} ({dryrun,notify=})")
            if dryrun:
                continue
            await _modify_user(valid_member, attribs={removal_scheduled_user_attr_name: None})
            if not notify or not removal_averted_message:
                continue
            address = notification_redirect_addr or f"{valid_member}@icecube.wisc.edu"
            logger.info(f"Sending 'removal averted' notification to {address} ({dryrun,notify=})")
            # noinspection PyTypeChecker
            send_email(address, f"You are no longer scheduled for removal from {target_path}",
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
                    logger.debug(f"Too early to remove {extraneous_member} {removal_scheduled_at_str=}")
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
                    continue
                address = notification_redirect_addr or f"{extraneous_member}@icecube.wisc.edu"
                logger.info(f"Sending 'scheduled for removal' notification to {address} ({dryrun,notify=})")
                # noinspection PyTypeChecker
                send_email(address, f"You are scheduled for removal from {target_path}",
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
            continue
        address = notification_redirect_addr or f"{extraneous_member}@icecube.wisc.edu"
        logger.info(f"Sending 'removal occurred' notification to {address} ({dryrun,notify=})")
        # noinspection PyTypeChecker
        send_email(address, f"You have been removed from {target_path}",
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
        send_email(address, f"You have been added to {target_path}",
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
                        help="send email notifications if using --manual")
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    if args['no_email'] and args['auto']:
        logger.critical("--no-email is incompatible with --auto")
        parser.exit(1)

    keycloak_client = get_rest_client()

    if args['auto']:
        return asyncio.run(auto_sync(
            keycloak_client=keycloak_client,
            dryrun=args['dryrun']))
    else:
        return asyncio.run(manual_sync(args['sync_spec'][0],
                                       args['sync_spec'][1],
                                       keycloak_client=keycloak_client,
                                       notify=args['notify'],
                                       dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
