"""
Sync membership of the target composite group(s) to match the union of
the memberships of their constituent source groups.

Paths of the constituent groups are specified as a JSONPath expression
to be applied to the complete Keycloak group hierarchy (list of trees
of all groups with one tree per top-level group).

Runtime configuration options are specified for each composite group as
custom group attributes. See documentation of the `sync_composite_groups_*`
attributes for the available configuration options (link to documentation
below).

The target composite group(s) and the JSONPath specifications of their
constituents are either provided on the command line (manual mode) or
discovered automatically (automatic mode).

Manual mode is intended mostly for testing and debugging (e.g. of JSONPath
expressions), but could be useful for initial silent seeding of composite
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
from typing import List

from krs.email import send_email
from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group, get_group_hierarchy, list_groups
from krs.token import get_rest_client
from krs.users import user_info, modify_user


logger = logging.getLogger('sync_composite_groups')


async def manual_sync(target_path: str,
                      constituents_expr: str,
                      /, *,
                      keycloak_client: ClientCredentialsAuth,
                      no_email: bool = False,
                      dryrun: bool = False):
    target_group = await group_info(target_path)
    attrs = target_group['attributes']
    if attrs.get('sync_composite_groups_enable'):
        logger.critical(f"To operate in manual mode, {target_path}'s "
                        f"sync_composite_groups_enable attribute must be empty or absent")
        return 1
    if group_cons_expr := attrs.get('sync_composite_groups_constituents_expr'):
        if group_cons_expr != constituents_expr:
            logger.critical(f"To operate in manual mode, {target_path}'s "
                            f"sync_composite_groups_constituents_expr must be empty, absent, "
                            f"or equal to the expression given on the command line")
    attrs['sync_composite_groups_constituents_expr'] = constituents_expr

    return await sync_composite_group(target_path,
                                      attrs['sync_composite_groups_constituents_expr'],
                                      attrs,
                                      keycloak_client=keycloak_client,
                                      dryrun=dryrun,
                                      no_email=no_email)


async def auto_sync(keycloak_client, dryrun):
    # At the moment, it's faster to list all groups and pick the ones
    # we need in python, than to query groups via REST API
    all_groups = await list_groups(rest_client=keycloak_client)
    enabled_group_paths = [v['path'] for v in all_groups.values()
                           if v.get('attributes', {}).get('sync_composite_groups_enable') == 'true']

    for enabled_group_path in enabled_group_paths:
        enabled_group = await group_info(enabled_group_path, rest_client=keycloak_client)
        attrs = enabled_group['attributes']
        await sync_composite_group(enabled_group_path,
                                   attrs['sync_composite_groups_constituents_expr'],
                                   attrs,
                                   keycloak_client=keycloak_client,
                                   dryrun=dryrun)


async def sync_composite_group(target_path: str,
                               constituents_expr: str,
                               opts: dict,
                               /, *,
                               keycloak_client: ClientCredentialsAuth,
                               dryrun: bool = False,
                               no_email: bool = False):
    """Sync (add/remove) members of group at `destination_path` to the union of the
    memberships of groups specified by `source_specs`.

    See argparse help and file docstring for documentation.

    Args:
        constituents_expr (List[List[str]]): list of (ROOT_GROUP_PATH, JSONPATH_EXPR) pairs
        opts (dict): XXX
        target_path (str): path to the destination group
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
        no_email (bool): XXX
    """
    # Set up partials to make the code easier to read
    _get_group_hierarchy = partial(get_group_hierarchy, rest_client=keycloak_client)
    _get_group_membership = partial(get_group_membership, rest_client=keycloak_client)
    _user_info = partial(user_info, rest_client=keycloak_client)
    _modify_user = partial(modify_user, rest_client=keycloak_client)
    _remove_user_group = partial(remove_user_group, rest_client=keycloak_client)
    _add_user_group = partial(add_user_group, rest_client=keycloak_client)

    # Build the list of all constituent groups' paths
    group_hierarchy = _get_group_hierarchy()
    source_group_paths = [v.value for v in parse(constituents_expr).find(group_hierarchy)]
    logger.debug(f"Syncing {target_path} to {source_group_paths}")

    # Determine what the current membership is and what it should be
    current_members = set(await _get_group_membership(target_path))
    target_members_lists = [await _get_group_membership(source_group_path)
                            for source_group_path in source_group_paths]
    target_members = set(chain.from_iterable(target_members_lists))

    # Get all config values into own variables to make code easier to read
    removal_scheduled_user_attr_name = f"{target_path}_removal_scheduled_at"
    removal_grace_days = opts.get('sync_composite_groups_member_removal_grace_days')
    removal_pending_message = (opts.get('sync_composite_groups_member_removal_pending_message', '')
                               .replace('@@', '\n'))
    removal_averted_message = (opts.get('sync_composite_groups_member_removal_averted_message', '')
                               .replace('@@', '\n'))
    removal_occurred_message = (opts.get('sync_composite_groups_member_removal_occurred_message', '')
                                .replace('@@', '\n'))
    welcome_message = opts.get('sync_composite_groups_member_welcome_message', '').replace('@@', '\n')
    notification_email_cc = opts.get('sync_composite_groups_notification_email_cc')

    # Reset removal grace times of normal members (will be set if they rejoined a
    # constituent group before removal grace period expired)
    for current_member in current_members:
        user = await _user_info(current_member)
        attrs = user['attributes']
        if attrs.get(removal_scheduled_user_attr_name):
            logger.info(f"Clearing {current_member}'s {removal_scheduled_user_attr_name} attribute ({dryrun=})")
            if dryrun:
                continue
            await _modify_user(current_member, attribs={removal_scheduled_user_attr_name: None})
            if not removal_averted_message or no_email:
                continue
            address = attrs.get('mailing_list_email') or f"{user['username']}@icecube.wisc.edu"
            send_email(address, f"You are no longer scheduled for removal from {target_path}",
                       removal_averted_message.format(
                           first_name=user['firstName'], email=address, group_path=target_path),
                       cc=notification_email_cc)

    # Process members that don't belong to any constituent group,
    # removing them if grace period undefined or expired
    for extraneous_member in current_members - target_members:
        logger.info(f"{extraneous_member} shouldn't be in {target_path} {dryrun=}")
        if dryrun:
            continue
        user = await _user_info(extraneous_member)
        attrs = user['attributes']

        if removal_grace_days:
            if removal_scheduled_at_str := attrs.get(removal_scheduled_user_attr_name):
                removal_scheduled_at = datetime.fromisoformat(removal_scheduled_at_str)
                # move on if too early to remove
                if datetime.now() < removal_scheduled_at + timedelta(days=removal_grace_days):
                    logger.debug(f"too early to remove {extraneous_member}")
                    continue
            else:
                # set "removal scheduled attribute" and move on
                removal_scheduled_at_str = datetime.now().isoformat()
                logger.info(f"Setting {extraneous_member}'s {removal_scheduled_user_attr_name} "
                            f"to {removal_scheduled_at_str}")
                await _modify_user(extraneous_member,
                                   attribs={removal_scheduled_user_attr_name:
                                            removal_scheduled_at_str})
                if no_email or not removal_pending_message:
                    continue
                address = attrs.get('mailing_list_email') or f"{user['username']}@icecube.wisc.edu"
                send_email(address, f"You are scheduled for removal from {target_path}",
                           removal_pending_message.format(
                               first_name=user['firstName'], email=address, group_path=target_path),
                           cc=notification_email_cc)
                continue
        # Either grace period not configured or grace period expired.
        # Remove the user from the group.
        await _modify_user(extraneous_member, attribs={removal_scheduled_user_attr_name: None})
        logger.info(f"removing {extraneous_member} from {target_path} {dryrun=}")
        await _remove_user_group(target_path, extraneous_member)
        if no_email or not removal_occurred_message:
            continue
        address = attrs.get('mailing_list_email') or f"{extraneous_member}@icecube.wisc.edu"
        send_email(address, f"You have been removed from {target_path}",
                   removal_occurred_message.format(
                       first_name=user['firstName'], email=address, group_path=target_path),
                   cc=notification_email_cc)

    # Add missing members to the group
    for missing_member in target_members - current_members:
        logger.info(f"adding {missing_member} to {target_path} {dryrun=}")
        if dryrun:
            continue
        await _add_user_group(target_path, missing_member)
        if no_email or not welcome_message:
            continue
        user = await _user_info(missing_member)
        attrs = user['attributes']
        address = attrs.get('mailing_list_email') or f"{missing_member}@icecube.wisc.edu"
        send_email(address, f"You have been added to {target_path}",
                   welcome_message.format(
                       first_name=user['firstName'], email=address, group_path=target_path),
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
    parser.add_argument('--no-email', action='store_true',
                        help="don't send email notifications if using --manual")
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
                                       no_email=args['no_email'],
                                       dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
