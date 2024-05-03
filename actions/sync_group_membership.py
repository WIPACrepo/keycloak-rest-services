"""
Sync membership of the specified destination group to match the union of members
of the source groups, defined as a JSONPath expression applied to the group
hierarchy at the specified root group.

Originally written to automate management of some /mail/ subgroups (mailing lists).

Attribute filter expressions may use custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.sync_group_membership \
        --source \
            /institutions/IceCube \
            '$.subGroups[?attributes.authorlist == "true"].subGroups[?name =~ "^authorlist.*"].path' \
        --destination /mail/authorlist-test \
        --dryrun
"""

import asyncio
import logging
from itertools import chain
from jsonpath_ng.ext import parse  # type: ignore
from rest_tools.client.client_credentials import ClientCredentialsAuth
from typing import List

from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group
from krs.token import get_rest_client


logger = logging.getLogger('sync_group_members')


async def sync_group_membership(source_group_specs: List[List[str]],
                                destination_group_path: str,
                                /, *,
                                keycloak_client: ClientCredentialsAuth,
                                dryrun: bool = False):
    """Sync (add/remove) members of group at `destination_path` to the union of the
    memberships of groups specified by `source_specs`.

    See argparse help and file docstring for documentation.

    Args:
        source_group_specs (List[List[str]]): list of (ROOT_GROUP_PATH, JSONPATH_EXPR) pairs
        destination_group_path (str): path to the destination group
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Build the list of all source group paths
    source_group_paths = []
    for root_source_group_path, jsonpath_expr in source_group_specs:
        root_source_group = await group_info(root_source_group_path, rest_client=keycloak_client)  # type: ignore
        source_group_path_matches = [v.value for v in
                                     parse(jsonpath_expr).find(root_source_group)]  # type: ignore
        source_group_paths.extend(source_group_path_matches)

    logger.debug(f"Syncing {destination_group_path} to {source_group_paths}")

    # Determine what the current membership is and what it should be
    current_members = set(await get_group_membership(destination_group_path, rest_client=keycloak_client))
    target_members_lists = [await get_group_membership(source_group_path, rest_client=keycloak_client)
                            for source_group_path in source_group_paths]
    target_members = set(chain.from_iterable(target_members_lists))

    # Update membership
    for extraneous_member in current_members - target_members:
        logger.info(f"removing {extraneous_member} from {destination_group_path} {dryrun=}")
        if not dryrun:
            await remove_user_group(destination_group_path, extraneous_member, rest_client=keycloak_client)

    for missing_member in target_members - current_members:
        logger.info(f"adding {missing_member} to {destination_group_path} {dryrun=}")
        if not dryrun:
            await add_user_group(destination_group_path, missing_member, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync membership of the specified destination group to match the union '
                    'of members of the source groups, defined as a jsonpath expression '
                    'applied to the group hierarchy of the specified root group. '
                    'See file docstring for details and examples.',
        epilog="This code uses the extended JSONPath parser from the `jsonpath_ng` module. "
               "For JSONPath syntax and expressions, see https://github.com/h2non/jsonpath-ng/.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--source', nargs=2, metavar=('ROOT_PATH', 'JSONPATH_EXPR'), action='append',
                        help="source group(s), defined as a JSONPath expression JSONPATH_EXPR "
                             "to be applied to the Keycloak group hierarchy rooted at ROOT_PATH. "
                             "The expression must evaluate to a list of absolute group paths. "
                             "Hints: "
                             "(1) --source may be used multiple times. "
                             "(2) to use the group at ROOT_PATH itself as a source, set the "
                             "JSONPATH_EXPR to be `$.path`. "
                             "(3) See epilog for more information. "
                             "(4) See file docstring for a good example of a non-trivial "
                             "JSONPath expression.")
    parser.add_argument('--destination', metavar='PATH',
                        help='target group path')
    parser.add_argument('--auto', metavar='ROOT_PATH',
                        help='automatically sync direct subgroups of ROOT_PATH using configuration '
                             'stored in their attributes')
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(sync_group_membership(
        args['source'],
        args['destination'],
        keycloak_client=keycloak_client,
        dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
