"""
Sync membership of the specified destination group to the union of members
of the source groups defined as a jsonpath expression applied to the group
hierarchy of the specified root group.

Originally written to automate management of some /mail/ subgroups (mailing lists).

Attribute filter expressions may use custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.sync_group_membership \
        --root-group /institutions/IceCube \
        --source-groups '$.subGroups[?attributes.authorlist == "true"].subGroups[?name =~ "^authorlist.*"].path' \
        --destination /mail/authorlist \
        --dryrun
"""
import asyncio
import logging
from jsonpath_ng import parse
from itertools import chain

from rest_tools.client.client_credentials import ClientCredentialsAuth

from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group
from krs.institutions import list_insts
from krs.token import get_rest_client


logger = logging.getLogger('sync_group_members')

# all_groups = await list_groups(rest_client=kc)
# [(k,v) for k,v in all_groups.items() if k.count('/') == 1]

# XXX parse('$.subGroups[*].subGroups[*].subGroups[?name = "authorlist"]').find(insts)
# [v.value for v in parse("$.subGroups[*].subGroups[?name != '_admin']").find(insts)]
# [v.value for v in parse("$.subGroups[*].subGroups[?attributes.authorlist == 'true']").find(insts)]
# [v.value for v in parse("$.subGroups[*].subGroups[?attributes.authorlist == 'true'].path").find(insts)]
# [v.value for v in parse("$.subGroups[?path == '/institutions/IceCube-Gen2'].subGroups[?attributes.authorlist == \"true\"].path").find(insts)]
# --source - groups '$.subGroups[?path == "/institutions/IceCube"].subGroups[?attributes.authorlist == "true"].subGroups[?name =~ "^authorlist.*"].path'


async def sync_authors_mail_group(source_experiment: str,
                                  authors_mail_group_path: str,
                                  /, *,
                                  keycloak_client: ClientCredentialsAuth,
                                  dryrun: bool = False):
    """Sync (add/remove) members of `authors_mail_group_path` to the union of
    members of "authorlist*" subgroups of institution groups with `authorlist`
    attribute set to 'true that are part of source_experiment.

    Args:
        source_experiment (str): name of the experiment to consider
        authors_mail_group_path (str): path to the group we are supposed to sync
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    # Build the current set of authors from IceCube institutions with enabled authorlists
    institution_paths = await list_insts(source_experiment, rest_client=keycloak_client)
    enabled_institution_paths = [k for k, v in institution_paths.items()
                                 if v.get('authorlist') == 'true']
    logger.debug(f"{enabled_institution_paths=}")

    institution_groups = [await group_info(inst_path, rest_client=keycloak_client)
                          for inst_path in enabled_institution_paths]
    authorlist_groups = [inst_subgroup for inst_group in institution_groups
                         for inst_subgroup in inst_group['subGroups']
                         if inst_subgroup['name'].startswith('authorlist')]
    logger.debug(f"{authorlist_groups=}")

    actual_authors_lists = [await get_group_membership(authorlist_group['path'], rest_client=keycloak_client)
                            for authorlist_group in authorlist_groups]
    actual_authors = set(chain.from_iterable(actual_authors_lists))
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
        description='Sync (add/remove) members of the given mail group to the union of '
                    'members of the "authorlist*" subgroups of all institutions whose '
                    'attribute `authorlist is "true" that belong to the give experiment. '
                    'This script was originally written to keep up-to-date /mail/authors '
                    'and /mail/authors-gen2. See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--source-experiment', metavar='NAME', required=True,
                        help="the experiment whose authorlist* groups should be considered")
    parser.add_argument('--target-group', metavar='PATH', required=True,
                        help='target group')
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(sync_authors_mail_group(
        args['source_experiment'],
        args['target_group'],
        keycloak_client=keycloak_client,
        dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
