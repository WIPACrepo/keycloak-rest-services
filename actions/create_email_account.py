"""
Creates email accounts on the IceCube mail server.

Note that this uses ssh to remotely create email accounts.

Example::

    python actions/create_email_account.py --email-server mail.icecube.wisc.edu
"""
import logging
import asyncio
import pathlib
import tempfile
import subprocess
import json

from krs.groups import get_group_membership
from krs.users import list_users
from krs.token import get_rest_client
from krs.rabbitmq import RabbitMQListener
import actions.util

logger = logging.getLogger('create_email_account')


async def process(email_server, group_path, keycloak_client=None):
    group_members = await get_group_membership(group_path, rest_client=keycloak_client)
    all_users = await list_users(rest_client=keycloak_client)

    users = {}
    for username in group_members:
        user = all_users[username]
        users[username] = {
            'firstName': user['firstName'],
            'lastName': user['lastName'],
        }

    script = f'''import subprocess
users = {json.dumps(users)}
with open('/etc/postfix/local_recipients') as f:
    current_users = set([line.split()[0] for line in f.readlines() if line and 'OK' in line])

changes = False
for username in users:
    if username in current_users:
        continue
    changes = True
    with open('/etc/postfix/canonical_sender', 'a') as f:
        f.write(username+'     '+users[username]['firstName']+'.'+users[username]['lastName']+'\n')
    with open('/etc/postfix/canonical_recipient', 'a') as f:
        f.write(users[username]['firstName']+'.'+users[username]['lastName']+'     '+username+'\n')
    with open('/etc/postfix/local_recipients', 'a') as f:
        f.write(username+'     OK\n')

if changes:
    subprocess.call('/usr/bin/sudo /usr/sbin/postmap /etc/postfix/canonical_recipient', shell=True)
    subprocess.call('/usr/bin/sudo /usr/sbin/postmap /etc/postfix/canonical_sender', shell=True)
    subprocess.call('/usr/bin/sudo /usr/sbin/postmap /etc/postfix/local_recipients', shell=True)
    subprocess.call('/usr/sbin/postfix reload', shell=True)
'''
    actions.util.scp_and_run(email_server, script, script_name='create_email_accounts.py')

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
    parser.add_argument('--log_level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true', help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')
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
        asyncio.run(process(args['email_server'], args['group_path'], keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
