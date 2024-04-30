"""
Sync membership of /mail/icecube-c to the union of members of direct subgroups
of /institutions/IceCube.

Originally written to maintain /mail/icecube-c (IceCube collaboration mail group).

Example::
    python -m actions.sync_icecube-c_group --dryrun
"""
import asyncio
import logging
from itertools import chain

from rest_tools.client.client_credentials import ClientCredentialsAuth

from krs.groups import get_group_membership, group_info, remove_user_group, add_user_group
from krs.institutions import list_insts
from krs.token import get_rest_client

logger = logging.getLogger('sync_icecube-c_mail_group')


async def sync_icecube_c_mail_group(*, keycloak_client: ClientCredentialsAuth, dryrun: bool = False):
    """Sync (add/remove) members of /mail/icecube-c to the union of
    members of direct subgroups of /institutions/IceCube.

    Args:
        keycloak_client (ClientCredentialsAuth): REST client to the KeyCloak server
        dryrun (bool): perform a trial run with no changes made
    """
    institution_paths = await list_insts("IceCube", rest_client=keycloak_client)
    logger.debug(f"{institution_paths=}")

    institution_groups = [await group_info(inst_path, rest_client=keycloak_client)
                          for inst_path in institution_paths]
    logger.debug(f"{institution_groups=}")

    actual_member_lists = [await get_group_membership(institution_group['path'], rest_client=keycloak_client)
                           for institution_group in institution_groups]
    actual_members = set(chain.from_iterable(actual_member_lists))
    logger.debug(f"{actual_members=}")

    current_members = set(await get_group_membership('/mail/icecube-c', rest_client=keycloak_client))
    logger.debug(f"{current_members=}")

    # Update membership
    for extraneous_member in current_members - actual_members:
        logger.info(f"removing {extraneous_member} from /mail/icecube-c {dryrun=}")
        if not dryrun:
            await remove_user_group("/mail/icecube-c", extraneous_member, rest_client=keycloak_client)

    for missing_member in actual_members - current_members:
        logger.info(f"adding {missing_member} to /mail/icecube-c {dryrun=}")
        if not dryrun:
            await add_user_group("/mail/icecube-c", missing_member, rest_client=keycloak_client)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Sync (add/remove) members /mail/icecube-c to the union of '
                    'members of the direct subgroups of /institutions/IceCube.'
                    'See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dryrun', action='store_true',
                        help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(sync_icecube_c_mail_group(
        keycloak_client=keycloak_client,
        dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
