"""
Creates a user directory for anyone with a POSIX account.

Creates directories of the style /<rootdir>/<username> relative
to a root directory.

Example::

    python actions/create_user_directory.py --root-dir /foo/bar

This will create user dirs with directories like `/foo/bar/user1`.

"""
import os
import logging
import asyncio
import getpass
import pathlib
import subprocess

from krs.groups import get_group_membership
from krs.users import list_users
from krs.token import get_rest_client
from krs.rabbitmq import RabbitMQListener

from .util import QUOTAS


logger = logging.getLogger('create_user_directory')


async def process(group_path, root_dir, keycloak_client=None):
    group_members = await get_group_membership(group_path, rest_client=keycloak_client)
    users = await list_users(rest_client=keycloak_client)
    is_root = getpass.getuser() == 'root'
    if not is_root:
        logger.debug('Running as user ' + getpass.getuser())
        logger.debug('Will not chown or set quota')

    for username in group_members:
        user = users[username]
        if 'attributes' in user and 'uidNumber' in user['attributes'] and 'gidNumber' in user['attributes']:
            path = root_dir / username
            if not path.exists():
                logger.info(f'Creating directory {path}')
                path.mkdir(mode=0o755, parents=True, exist_ok=True)
                if is_root:
                    logging.debug(f'Changing ownership of {path} to {user["attributes"]["uidNumber"]}:{user["attributes"]["gidNumber"]}')
                    os.chown(path, int(user['attributes']['uidNumber']), int(user['attributes']['gidNumber']))
                    if root_dir in QUOTAS:
                        logging.debug(f'Setting quota on directory {path}')
                        attrs = {
                            'uid': user['attributes']['uidNumber'],
                            'gid': user['attributes']['gidNumber'],
                        }
                        subprocess.check_call(QUOTAS[root_dir].format(**attrs), shell=True)


def listener(group_path, address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']['path'] == group_path:
            await process(group_path=group_path, **kwargs)

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

    parser = argparse.ArgumentParser(description='Create home directories')
    parser.add_argument('group_path', default='/posix', help='group path (/parentA/parentB/name)')
    parser.add_argument('--root-dir', default='/', type=pathlib.Path, help='root directory to create home user directories in (default=/)')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true', help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    if args['listen']:
        ret = listener(address=args['listen_address'], exchange=args['listen_exchange'],
                       group_path=args['group_path'], root_dir=args['root_dir'],
                       keycloak_client=keycloak_client)
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['group_path'], args['root_dir'], keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
