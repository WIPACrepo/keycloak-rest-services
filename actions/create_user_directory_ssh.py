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
import json
import pathlib
import subprocess

from krs.groups import get_group_membership
from krs.users import list_users
from krs.token import get_rest_client
from krs.rabbitmq import RabbitMQListener
import actions.util


logger = logging.getLogger('create_user_directory')


async def process(server, group_path, root_dir, mode=0o755, keycloak_client=None):
    group_members = await get_group_membership(group_path, rest_client=keycloak_client)
    users = await list_users(rest_client=keycloak_client)

    user_dirs = {}
    for username in group_members:
        user = users[username]
        if 'attributes' in user and 'uidNumber' in user['attributes'] and 'gidNumber' in user['attributes']:
            user_dirs[username] = {
                'path': str(root_dir / username),
                'uid': int(user['attributes']['uidNumber']),
                'gid': int(user['attributes']['gidNumber']),
            }

    script = f'''import subprocess
import os
import getpass
import logging
logging.basicConfig(level={logging.getLogger().getEffectiveLevel()})

user_dirs = {json.dumps(user_dirs)}
QUOTAS = {json.dumps(actions.util.QUOTAS)}

existing = os.listdir('{root_dir}')
is_root = getpass.getuser() == 'root'
if not is_root:
    logging.debug('running as user ' + getpass.getuser())
    logging.debug('will not chown or set quota')

for username in set(user_dirs).difference(existing):
    path = user_dirs[username]['path']
    if not os.path.exists(path):
        logging.info('Creating directory ' + path)
        os.makedirs(path, mode={mode})
        if is_root:
            logging.debug('Changing ownership of %s to %d:%d', path,
                          user_dirs[username]['uid'], user_dirs[username]['gid'])
            os.chown(path, user_dirs[username]['uid'], user_dirs[username]['gid'])
            if root_dir in QUOTAS:
                logging.debug('Setting quota on directory ' + path)
                subprocess.check_call(QUOTAS[root_dir].format(user_dirs[username]['uid']), shell=True)
'''
    actions.util.scp_and_run_sudo(server, script, script_name='create_directory.py')



def listener(group_path, address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']['path'] == group_path:
            await process(group_path=group_path, **kwargs)

    args = {
        'routing_key': 'KK.EVENT.ADMIN.#.GROUP_MEMBERSHIP.#',
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
                            mode=args['mode'], keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
