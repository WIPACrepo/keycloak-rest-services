"""
Remove from KeyCloak mailing list groups users who are not part of those groups'
experiment.

This code assumes that the mailing list group hierarcy is structured likes this:
/ROOT_MAILING_LIST_GROUP
    /EXPERIMENT_NAME
        /MAILING_LIST_NAME
        ...
    ...

EXPERIMENT_NAME must match group names of experiments under the /institutions
group hierarchy because that is how this code determines which experiment a
mailing list group belongs to.


Example::

       python -m actions.deprovision_mailing_lists --ml-group-root /test-mail
"""
import asyncio
import logging

from krs.rabbitmq import RabbitMQListener
from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, remove_user_group
from krs.institutions import list_insts


logger = logging.getLogger('deprovision_mailing_lists')


async def process(mailing_list_group_root, keycloak_client, dryrun=False):
    """Remove from all mailing list groups users who are not part of the
    experiment the mailing list belongs to.

    Active users of an experiment are determined by examining the /institutions
    group hierarchy. It is assumed that experiment group names under /institutions
    match exactly experiment group names under mailing_list_group_root.

    Args:
        mailing_list_group_root (str): KeyCloak path to mailing list group tree
        keycloak_client (RestClient): KeyCloak REST API client
        dryrun (bool): perform a mock run with no changes made
    """
    institutions = await list_insts(rest_client=keycloak_client)
    experiment_usernames = {}
    for inst_group_path in institutions.keys():
        exp = inst_group_path.split('/')[2]
        exp_users = await get_group_membership(inst_group_path, rest_client=keycloak_client)
        experiment_usernames[exp] = set(exp_users)

    root_group = await group_info(mailing_list_group_root, rest_client=keycloak_client)
    exp_groups = root_group['subGroups']

    for exp_group in exp_groups:
        exp = exp_group['name']
        if exp not in experiment_usernames:
            logger.error(f'Unknown mailing list experiment {exp}. Skipping {exp_group["path"]} tree')
            continue
        for ml_group in exp_group['subGroups']:
            usernames = set(await get_group_membership(ml_group['path'], rest_client=keycloak_client))
            departed_usernames = usernames - experiment_usernames[exp]
            for username in departed_usernames:
                logger.info(f'Removing {username} from group {ml_group["path"]} (dryrun={dryrun})')
                if not dryrun:
                    await remove_user_group(ml_group['path'], username, rest_client=keycloak_client)


def listener(address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']:
            await process(**kwargs)

    args = {
        'routing_key': 'KK.EVENT.ADMIN.#.SUCCESS.GROUP_MEMBERSHIP.#',
        'dedup': dedup,
    }
    if address:
        args['address'] = address
    if exchange:
        args['exchange'] = exchange

    return RabbitMQListener(action, **args)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Remove from KeyCloak mailing list groups users who are not part of '
                    'those groups\' experiment.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--ml-group-root', metavar='GROUP_PATH', default='/mailing-lists',
                        help='root of the mailing list group tree')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true',
                        help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    if args['listen']:
        ret = listener(address=args['listen_address'],
                       exchange=args['listen_exchange'],
                       mailing_list_group_root=args['ml_group_root'],
                       keycloak_client=keycloak_client,
                       dryrun=args['dryrun'])
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['ml_group_root'], keycloak_client, args['dryrun']))


if __name__ == '__main__':
    main()
