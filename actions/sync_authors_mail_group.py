"""

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

logger = logging.getLogger('sync_authorlist_mailing_group')


async def sync_authors_mail_group(authors_mail_group_path, keycloak_client=None, dryrun=False):
    """Update institutions_last_seen and institutions_last_changed user attributes.

    Args
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        notify (bool): send out notification emails
        dryrun (bool): perform a trial run with no changes made
    """
    icecube_group = await group_info('/institutions/IceCube', rest_client=keycloak_client)
    institution_groups = [inst_group for inst_group in icecube_group['subGroups']
                          if inst_group['attributes'].get('authorlist') == 'true']
    authorlist_groups = [inst_subgroup for inst_group in institution_groups
                         for inst_subgroup in inst_group['subGroups']
                         if inst_subgroup['name'] == 'authorlist']
    target_authors = [await get_group_membership(authorlist_group['path'], rest_client=keycloak_client)
                      for authorlist_group in authorlist_groups]
    target_authors = set(chain.from_iterable(target_authors))
    current_authors = set(await get_group_membership(authors_mail_group_path, rest_client=keycloak_client))

    for extraneous_author in current_authors - target_authors:
        logger.info(f"removing {extraneous_author} from {authors_mail_group_path} dryrun={dryrun}")
        if not dryrun:
            await remove_user_group(authors_mail_group_path, extraneous_author, rest_client=keycloak_client)

    for missing_author in target_authors - current_authors:
        logger.info(f"adding {missing_author} from {authors_mail_group_path} dryrun={dryrun}")
        if not dryrun:
            await add_user_group(authors_mail_group_path, missing_author, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Update institutions_last_seen and institutions_last_changed user '
                    'attributes. See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--target-group', metavar='PATH', default='/mail/authors',
                        help='target group')
    parser.add_argument('--dryrun', action='store_true', help='dry run (implies no notifications)')
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
