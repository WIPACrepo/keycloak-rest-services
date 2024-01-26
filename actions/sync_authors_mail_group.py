"""
Sync (add/remove) membership of the group /mail/authors (or group specified
on command line) to the union of members of "authorlist" subgroups of all
institution of the IceCube experiment whose attribute `authorlist` is 'true'.

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.sync_authors_mail_group --dryrun
"""
import asyncio
import logging
from itertools import chain

from rest_tools.client.client_credentials import ClientCredentialsAuth

from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group
from krs.institutions import list_insts
from krs.token import get_rest_client

logger = logging.getLogger('sync_authors_mailing_group')


async def sync_authors_mail_group(authors_mail_group_path: str,
                                  /, *,
                                  keycloak_client: ClientCredentialsAuth,
                                  dryrun: bool = False):
    """Sync (add/remove) members of `authors_mail_group_path` (should be
    /mail/authors, unless debugging) to the union of members of "authorlist"
    subgroups of institution groups with `authorlist` attribute set to 'true'
    that are part of the IceCube experiment.

    Args:
        authors_mail_group_path (str): path to the group we are supposed to sync
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Build the current set of authors from IceCube institutions with enabled authorlists
    inst_paths = await list_insts('IceCube', rest_client=keycloak_client)
    enabled_inst_paths = [k for k, v in inst_paths.items() if v.get('authorlist') == 'true']
    logger.debug(f"{enabled_inst_paths=}")

    institution_groups = [await group_info(inst_path, rest_client=keycloak_client)
                          for inst_path in enabled_inst_paths]
    authorlist_groups = [inst_subgroup for inst_group in institution_groups
                         for inst_subgroup in inst_group['subGroups']
                         if inst_subgroup['name'] == 'authorlist']
    logger.debug(f"{authorlist_groups=}")

    actual_authors = [await get_group_membership(authorlist_group['path'], rest_client=keycloak_client)
                      for authorlist_group in authorlist_groups]
    actual_authors = set(chain.from_iterable(actual_authors))
    logger.debug(f"{actual_authors=}")

    current_authors = set(await get_group_membership(authors_mail_group_path, rest_client=keycloak_client))
    logger.debug(f"{current_authors=}")

    # Update membership
    for extraneous_author in current_authors - actual_authors:
        logger.info(f"removing {extraneous_author} from {authors_mail_group_path} {dryrun=}")
        if not dryrun:
            await remove_user_group(authors_mail_group_path, extraneous_author, rest_client=keycloak_client)

    for missing_author in actual_authors - current_authors:
        logger.info(f"adding {missing_author} to {authors_mail_group_path} {dryrun=}")
        if not dryrun:
            await add_user_group(authors_mail_group_path, missing_author, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync (add/remove) membership of the group /mail/authors '
                    '(unless overridden) to the union of members of "authorlist" '
                    'subgroups of all institution of the IceCube experiment '
                    'whose attribute `authorlist` is "true".',
        epilog="See module docstring for details.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--target-group', metavar='PATH', default='/mail/authors',
                        help='target group')
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(sync_authors_mail_group(
        args['target_group'],
        keycloak_client=keycloak_client,
        dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
