"""
Creates a user directory for anyone with a POSIX account.

Creates directories of the style /<rootdir>/<username> relative
to a root directory.

Example::

    python actions/create_user_directory.py --root-dir /foo/bar

This will create user dirs with directories like `/foo/bar/user1`.

"""
import asyncio
import json
import logging
import pathlib

from krs.groups import get_group_membership
from krs.users import list_users
from krs.token import get_rest_client
from krs.rabbitmq import RabbitMQListener
import actions.util


logger = logging.getLogger('create_user_directory_ssh')


async def process(server, group_path, root_dir, mode=0o755, dryrun=False, keycloak_client=None):
    skip_roles = actions.util.INGORE_DIR_ROLES.get(str(root_dir), [])
    group_members = await get_group_membership(group_path, rest_client=keycloak_client)
    users = await list_users(rest_client=keycloak_client)

    user_dirs = {}
    for username in group_members:
        attrs = users[username].get('attributes', {})
        if any(attrs.get(r, False) == 'True' for r in skip_roles):
            logger.debug(f'skipping user {username} for ignored role')
            continue
        if 'uidNumber' in attrs and 'gidNumber' in attrs:
            user_dirs[username] = {
                'path': str(root_dir / username),
                'uid': int(attrs['uidNumber']),
                'gid': int(attrs['gidNumber']),
                'username': username,
            }

    script = f'''import subprocess
import os
import getpass
import logging
logging.basicConfig(level={logger.getEffectiveLevel()})

root_dir = '{root_dir}'
user_dirs = {json.dumps(user_dirs)}
QUOTAS = {json.dumps(actions.util.QUOTAS)}
dryrun = {dryrun}

existing = os.listdir(root_dir)
is_root = getpass.getuser() == 'root'
if not is_root:
    logging.debug('Running as user ' + getpass.getuser())
    logging.debug('Will not chown or set quota')

for username in sorted(set(user_dirs).difference(existing)):
    path = user_dirs[username]['path']
    if not os.path.exists(path):
        logging.info('Creating directory ' + path)
        if not dryrun:
            os.makedirs(path, mode={mode})
        if is_root:
            logging.debug('Changing ownership of %s to %d:%d', path,
                          user_dirs[username]['uid'], user_dirs[username]['gid'])
            if not dryrun:
                os.chown(path, user_dirs[username]['uid'], user_dirs[username]['gid'])
            if root_dir in QUOTAS:
                logging.debug('Setting quota on directory ' + path)
                if not dryrun:
                    subprocess.check_call(QUOTAS[root_dir].format(**user_dirs[username]), shell=True)
'''
    actions.util.scp_and_run_sudo(server, script, script_name='create_directory.py')


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


def auto_int(x):
    return int(x, 0)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Create user directories via ssh')
    parser.add_argument('server', help='remote server')
    parser.add_argument('group_path', default='/posix', help='group path (/parentA/parentB/name)')
    parser.add_argument('--mode', default=0o755, type=auto_int, help='directory chmod mode (default: 755)')
    parser.add_argument('--root-dir', default='/', type=pathlib.Path, help='root directory to create home user directories in (default=/)')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true', help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    if args['listen']:
        ret = listener(address=args['listen_address'], exchange=args['listen_exchange'],
                       server=args['server'], group_path=args['group_path'],
                       root_dir=args['root_dir'], mode=args['mode'],
                       keycloak_client=keycloak_client)
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['server'], args['group_path'], args['root_dir'],
                            mode=args['mode'], dryrun=args['dryrun'],
                            keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
