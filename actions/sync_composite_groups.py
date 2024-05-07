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
from itertools import chain
from jsonpath_ng.ext import parse  # type: ignore
from rest_tools.client.client_credentials import ClientCredentialsAuth
from typing import List

from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group, get_group_hierarchy
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
                                      attrs,
                                      keycloak_client=keycloak_client,
                                      dryrun=dryrun,
                                      no_email=no_email)


def auto_sync(*args, **kwargs):
    pass


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
        target_path (str): path to the destination group
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Build the list of all source group paths
    group_hierarchy = get_group_hierarchy(rest_client=keycloak_client)
    source_group_paths = [v.value for v in parse(constituents_expr).find(group_hierarchy)]

    logger.debug(f"Syncing {target_path} to {source_group_paths}")

    # Determine what the current membership is and what it should be
    current_members = set(await get_group_membership(target_path, rest_client=keycloak_client))
    target_members_lists = [await get_group_membership(source_group_path, rest_client=keycloak_client)
                            for source_group_path in source_group_paths]
    target_members = set(chain.from_iterable(target_members_lists))

    removal_grace_user_attr_name = f"{target_path}_removal_grace_ends"
    removal_grace_days = opts.get('sync_composite_groups_member_removal_grace_days')

    # Reset removal grace times of normal members (will be set if they rejoined a
    # constituent group before removal grace period expired)
    for current_member in current_members:
        user = await user_info(current_member, rest_client=keycloak_client)
        if user['attributes'].get(removal_grace_user_attr_name):
            await modify_user(current_member, attribs={removal_grace_user_attr_name: None})

    # Process members that don't belong to any constituent group
    for extraneous_member in current_members - target_members:
        logger.info(f"{extraneous_member} shouldn't be in {target_path} {dryrun=}")
        if dryrun:
            continue
        user = await user_info(extraneous_member, rest_client=keycloak_client)
        if not removal_grace_days:
            await modify_user(extraneous_member, attribs={removal_grace_user_attr_name: None})
            logger.info(f"removing {extraneous_member} from {target_path} {dryrun=}")
            await remove_user_group(target_path, extraneous_member, rest_client=keycloak_client)

        else:
            if grace_ends_str := user['attributes'].get(removal_grace_user_attr_name):
                grace_ends = datetime.fromisoformat(grace_ends_str)
                if datetime.now() > grace_ends:
                    await modify_user(extraneous_member, attribs={removal_grace_user_attr_name: None})
                    logger.info(f"removing {extraneous_member} from {target_path} {dryrun=}")
                    await remove_user_group(target_path, extraneous_member, rest_client=keycloak_client)
                else:
                    logger.debug(f"too early to remove")
            else:
                # if removal grace attribute absent, set it
                # XXX what if no grace period
                removal_grace_date = datetime.now() + timedelta(days=removal_grace_days)
                await modify_user(extraneous_member,
                                  attribs={removal_grace_user_attr_name:
                                               removal_grace_date.isoformat()})


    for missing_member in target_members - current_members:
        logger.info(f"adding {missing_member} to {target_path} {dryrun=}")
        if not dryrun:
            await add_user_group(target_path, missing_member, rest_client=keycloak_client)


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
        logger.critical("--no-emails is incompatible with --auto")
        parser.exit(1)

    keycloak_client = get_rest_client()

    if args['auto']:
        return asyncio.run(manual_sync(args['sync_spec'][0],
                                args['sync_spec'][1],
                                keycloak_client=keycloak_client,
                                no_email=args['no_email'],
                                dryrun=args['dryrun']))
    else:
        return asyncio.run(auto_sync(
            keycloak_client=keycloak_client,
            no_email=args['no_email_notifications'],
            dryrun=args['dryrun']))


if __name__ == '__main__':
    sys.exit(main())
