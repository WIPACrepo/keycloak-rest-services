"""
Update users shadowExpire time in LDAP when their password changes.
"""
import asyncio
import logging
import string

from krs.ldap import LDAP
from krs.rabbitmq import RabbitMQListener


logger = logging.getLogger('update_ldap_shadow_expire')


ACCEPTABLE_LDAP_CN = string.ascii_letters+string.digits+'-_'


def flatten_group_name(path):
    path = path.replace('/', '-')
    path = ''.join(letter for letter in path if letter in ACCEPTABLE_LDAP_CN)
    return path


async def process(username=None, dryrun=False, ldap_client=None):
    ldap_users = ldap_client.list_users()

    if username:
        usernames = [username]
    else:
        usernames = list(ldap_users)

    for uid in sorted(usernames):
        user = ldap_users[uid]
        if 'shadowExpire' in user and 'shadowLastChange' in user and 'shadowMax' in user:

            oldExpire = int(user['shadowExpire'])
            newExpire = int(user['shadowLastChange'])+int(user['shadowMax'])

            if oldExpire > 0 and oldExpire < newExpire:
                logger.debug(f'old expire = {oldExpire}, lastChange = {user["shadowLastChange"]}')
                logger.info(f'updating expiry for user {uid} to {newExpire}')
                if not dryrun:
                    ldap_client.modify_user(uid, {'shadowExpire': newExpire})


def listener(group_path, address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        await process(message['representation']['username'], **kwargs)

    args = {
        'routing_key': 'KK.EVENT.ADMIN.#.SUCCESS.USER.#',
        'dedup': dedup,
    }
    if address:
        args['address'] = address
    if exchange:
        args['exchange'] = exchange

    return RabbitMQListener(action, **args)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update user shadowExpire in LDAP')
    parser.add_argument('--user', default=None, help='process a single user')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--listen', default=False, action='store_true', help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    ldap_client = LDAP()

    if args['listen']:
        ret = listener(address=args['listen_address'], exchange=args['listen_exchange'],
                       ldap_client=ldap_client)
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(args['user'], dryrun=args['dryrun'], ldap_client=ldap_client))


if __name__ == '__main__':
    main()
