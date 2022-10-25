"""
Sync specific group tree to LDAP.

Any Keycloak subgroups below the specified group will get synced to
an OU in LDAP.
"""
import asyncio
import logging
import string

from krs.groups import list_groups, get_group_membership_by_id
from krs.token import get_rest_client
from krs.ldap import LDAP, get_ldap_members
from krs.rabbitmq import RabbitMQListener


logger = logging.getLogger('sync_ldap_groups')


ACCEPTABLE_LDAP_CN = string.ascii_letters+string.digits+'-_'


def flatten_group_name(path):
    path = path.replace('/', '-')
    path = ''.join(letter for letter in path if letter in ACCEPTABLE_LDAP_CN)
    return path


async def process(group_path, ldap_ou=None, posix=False, recursive=False, dryrun=False, keycloak_client=None, ldap_client=None):
    ldap_groups = ldap_client.list_groups(groupbase=ldap_ou)
    ldap_users = ldap_client.list_users()

    if posix:
        # get highest gid in ldap
        max_gid = 0
        ldap_users = ldap_client.list_users(['gidNumber'])
        for username in ldap_users:
            user = ldap_users[username]
            if 'gidNumber' in user and user['gidNumber'] > max_gid:
                max_gid = user['gidNumber']
        for cn in ldap_groups:
            group = ldap_groups[cn]
            if 'gidNumber' in group and group['gidNumber'] > max_gid:
                max_gid = group['gidNumber']

    ret = await list_groups(rest_client=keycloak_client)
    groups = []
    for p in sorted(ret):
        if not p.startswith(group_path+'/'):
            continue
        elif ret[p]['name'].startswith('_'):
            continue
        elif (not recursive) and '/' in p[len(group_path)+1:]:
            continue
        groups.append(ret[p])

    for group in groups:
        ldap_cn = flatten_group_name(group['path'][len(group_path)+1:])
        logger.debug(f'working on group: {ldap_cn}')

        if ldap_cn not in ldap_groups:
            kwargs = {}
            if posix:
                max_gid += 1
                kwargs['gidNumber'] = max_gid
            if not dryrun:
                ldap_client.create_group(ldap_cn, groupbase=ldap_ou, **kwargs)

        keycloak_members = await get_group_membership_by_id(group['id'], rest_client=keycloak_client)
        logger.debug(f'  keycloak_members: {keycloak_members}')
        ldap_members = get_ldap_members(ldap_groups[ldap_cn] if ldap_cn in ldap_groups else {})
        logger.debug(f'  ldap_members: {ldap_members}')
        ldap_members = set(ldap_members).intersection(ldap_users)
        logger.debug(f'  ldap_members_users: {ldap_members}')

        add_members = set(keycloak_members) - set(ldap_members)
        if add_members:
            logger.info(f'adding members to group {ldap_cn}: {add_members}')
            if not dryrun:
                for member in add_members:
                    ldap_client.add_user_group(member, ldap_cn, groupbase=ldap_ou)

        remove_members = set(ldap_members) - set(keycloak_members)
        if remove_members:
            logger.info(f'removing members from group {ldap_cn}: {remove_members}')
            if not dryrun:
                for member in remove_members:
                    ldap_client.remove_user_group(member, ldap_cn, groupbase=ldap_ou)


def listener(group_path, address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']['path'] == group_path:
            await process(group_path, **kwargs)

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

    parser = argparse.ArgumentParser(description='Sync Keycloak groups to LDAP')
    parser.add_argument('group_path', default='/posix', help='parent group path (/parentA/parentB/name)')
    parser.add_argument('ldap_ou', default=None, help='LDAP OU for groups')
    parser.add_argument('--posix', default=False, action='store_true', help='enable posix group handling')
    parser.add_argument('--recursive', default=False, action='store_true', help='enable recursive syncing of nested groups')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true', help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    ldap_client = LDAP()

    if args['listen']:
        ret = listener(args['group_path'], ldap_ou=args['ldap_ou'], posix=args['posix'],
                       recursive=args['recursive'],
                       address=args['listen_address'], exchange=args['listen_exchange'],
                       keycloak_client=keycloak_client, ldap_client=ldap_client)
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['group_path'], ldap_ou=args['ldap_ou'],
                            posix=args['posix'], recursive=args['recursive'],
                            dryrun=args['dryrun'],
                            keycloak_client=keycloak_client,
                            ldap_client=ldap_client))


if __name__ == '__main__':
    main()
