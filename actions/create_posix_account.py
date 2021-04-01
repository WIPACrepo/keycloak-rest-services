"""
Creates a POSIX user account in LDAP for anyone in the specified Keycloak group.
"""
import logging
import asyncio

from krs.groups import get_group_membership
from krs.token import get_rest_client
from krs.ldap import LDAP
from krs.rabbitmq import RabbitMQListener


logger = logging.getLogger('create_posix_account')

async def process(group_path, keycloak_client=None, ldap_client=None):
    # get highest uid, gid in ldap
    max_uid = 0
    max_gid = 0
    users = ldap_client.list_users(['uidNumber', 'gidNumber', 'loginShell'])
    ldapPosix = set()
    for username in users:
        user = users[username]
        if 'uidNumber' in user and user['uidNumber'] > max_uid:
            max_uid = user['uidNumber']
        if 'gidNumber' in user and user['gidNumber'] > max_gid:
            max_gid = user['gidNumber']
        if 'loginShell' in user and user['loginShell'] and user['loginShell'] != '/sbin/nologin':
            ldapPosix.add(username)
    max_id = max(max_uid, max_gid)

    ret = await get_group_membership(group_path, rest_client=keycloak_client)

    # add new users
    for username in ret:
        if username in users and 'uidNumber' in users[username]:
            if 'loginShell' in user and user['loginShell'] and user['loginShell'] == '/sbin/nologin':
                # add back an existing account access
                attribs = {
                    'loginShell': '/bin/bash',
                }
                ldap_client.modify_user(username, attribs)
                logger.info(f're-enabled user {username} as a POSIX user')
        else:
            # new uid/gid
            max_id += 1
            user = users[username]
            shell = user['attributes']['loginShell'] if 'attributes' in user and 'loginShell' in user['attributes'] else '/bin/bash'
            attribs = {
                'uidNumber': max_id,
                'gidNumber': max_id,
                'homeDirectory': f'/home/{username}',
                'loginShell': shell,
            }
            ldap_client.modify_user(username, attribs, objectClass='posixAccount')
            logger.info(f'added user {username} as a POSIX user with {max_id}:{max_id}')

    # remove users that lost POSIX access
    for username in ldapPosix.difference(ret):
        attribs = {
            'loginShell': '/sbin/nologin',
        }
        ldap_client.modify_user(username, attribs)
        logger.info(f'disabled user {username} as a POSIX user')

    # sync with Keycloak
    await ldap_client.force_keycloak_sync(keycloak_client=keycloak_client)

def listener(group_path, address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']['path'] == group_path:
            await process(group_path, **kwargs)

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

    parser = argparse.ArgumentParser(description='Create POSIX accounts')
    parser.add_argument('group_path', default='/posix', help='group path (/parentA/parentB/name)')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true', help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    ldap_client = LDAP()

    if args['listen']:
        ret = listener(args['group_path'], address=args['listen_address'], exchange=args['listen_exchange'],
                       keycloak_client=keycloak_client, ldap_client=ldap_client)
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['group_path'], keycloak_client=keycloak_client, ldap_client=ldap_client))


if __name__ == '__main__':
    main()
