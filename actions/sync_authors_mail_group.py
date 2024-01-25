"""
XXX

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.track_user_institutions --dryrun
"""
import asyncio
import logging

from itertools import chain

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group

logger = logging.getLogger('sync_authors_mailing_group')


async def sync_authors_mail_group(authors_mail_group_path, /, *, keycloak_client=None, dryrun=False):
    """XXX

    Args:
        authors_mail_group_path (str): path to the group we are supposed to sync
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Build the set of all
    icecube_group = await group_info('/institutions/IceCube', rest_client=keycloak_client)
    institution_groups = [inst_group for inst_group in icecube_group['subGroups']
                          if inst_group['attributes'].get('authorlist') == 'true']
    authorlist_groups = [inst_subgroup for inst_group in institution_groups
                         for inst_subgroup in inst_group['subGroups']
                         if inst_subgroup['name'] == 'authorlist']
    legitimate_authors = [await get_group_membership(authorlist_group['path'], rest_client=keycloak_client)
                          for authorlist_group in authorlist_groups]
    legitimate_authors = set(chain.from_iterable(legitimate_authors))
    current_authors = set(await get_group_membership(authors_mail_group_path, rest_client=keycloak_client))

    for extraneous_author in current_authors - legitimate_authors:
        logger.info(f"removing {extraneous_author} from {authors_mail_group_path} {dryrun=}")
        if not dryrun:
            await remove_user_group(authors_mail_group_path, extraneous_author, rest_client=keycloak_client)

    for missing_author in legitimate_authors - current_authors:
        logger.info(f"adding {missing_author} to {authors_mail_group_path} {dryrun=}")
        if not dryrun:
            await add_user_group(authors_mail_group_path, missing_author, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='XXX',
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
