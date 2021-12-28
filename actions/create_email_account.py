"""
Creates email accounts on the IceCube mail server.

Note that this uses ssh to remotely create email accounts.

Example::

    python actions/create_email_account.py --email-server mail.icecube.wisc.edu
"""
import logging
import asyncio
import json

from krs.groups import get_group_membership
from krs.users import list_users
from krs.token import get_rest_client
from krs.rabbitmq import RabbitMQListener
import actions.util

logger = logging.getLogger('create_email_account')


async def process(email_server, group_path, dryrun=False, keycloak_client=None):
    group_members = await get_group_membership(group_path, rest_client=keycloak_client)
    all_users = await list_users(rest_client=keycloak_client)

    users = {}
    for username in group_members:
        user = all_users[username]
        attrs = user.get('attributes', {})
        if attrs.get('noIceCubeEmail', False) == 'True':
            continue
        if (not attrs.get('uid', False)) or (not attrs.get('gid', False)):
            logger.info(f'user {username} is not a posix user, skipping')
            continue
        users[username] = {
            'canonical': user['firstName'].lower()+'.'+user['lastName'].lower(),
            'uid': int(attrs['uid']),
            'gid': int(attrs['gid']),
        }

    script = f'''import subprocess
import logging
import os
logging.basicConfig(level={logger.getEffectiveLevel()})

users = {json.dumps(users)}
with open('/etc/postfix/local_recipients') as f:
    current_users = set([line.split()[0] for line in f.readlines() if line and 'OK' in line])
dryrun = {dryrun}

is_root = getpass.getuser() == 'root'
if not is_root:
    logging.debug('Running as user ' + getpass.getuser())
    logging.debug('Will not chown')

changes = False
for username in sorted(set(users)-current_users):
    logging.info('Adding email for user ' + username)
    changes = True
    user = users[username]
    if not dryrun:
        with open('/etc/postfix/canonical_sender', 'a') as f:
            f.write(username+'     '+user['canonical']+'\\n')
        with open('/etc/postfix/canonical_recipient', 'a') as f:
            f.write(user['canonical']+'     '+username+'\\n')
        with open('/etc/postfix/local_recipients', 'a') as f:
            f.write(username+'     OK\\n')

    path = '/mnt/mail/'+username
    if not os.path.exists(path):
        logging.debug('Creating directory ' + path)
        if not dryrun:
            os.makedirs(path, mode=0o755)
        if is_root:
            logging.debug('Changing ownership of %s to %d:%d', path,
                          user['uid'], user['gid'])
            if not dryrun:
                os.chown(path, user['uid'], user['gid'])

if changes and not dryrun:
    logging.info('reloading postfix')
    subprocess.check_call(['/usr/sbin/postmap', '/etc/postfix/canonical_recipient'])
    subprocess.check_call(['/usr/sbin/postmap', '/etc/postfix/canonical_sender'])
    subprocess.check_call(['/usr/sbin/postmap', '/etc/postfix/local_recipients'])
    subprocess.check_call(['/usr/sbin/postfix', 'reload'])
'''
    actions.util.scp_and_run_sudo(email_server, script, script_name='create_email_accounts.py')

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


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Create email accounts')
    parser.add_argument('group_path', default='/email', help='group path (/parentA/parentB/name)')
    parser.add_argument('--email-server', default='mail.icecube.wisc.edu', help='email server')
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
                       email_server=args['email_server'], group_path=args['group_path'],
                       keycloak_client=keycloak_client)
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['email_server'], args['group_path'],
                            dryrun=args['dryrun'], keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
