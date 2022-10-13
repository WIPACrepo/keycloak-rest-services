"""
Syncs user accounts from KeyCloak to Google Workspace.

Creates missing accounts, suspends disabled accounts, activates enabled accounts.

Example::

    python actions/sync_gws_users.py

This will sync all users from KeyCloak to Google Workspace.

"""
import asyncio
import logging
import random
import string

from googleapiclient.discovery import build
from google.oauth2 import service_account

from krs.users import list_users
from krs.token import get_rest_client
from krs.rabbitmq import RabbitMQListener

from pprint import pprint


logger = logging.getLogger('sync_gws_users')


def get_gws_users(gws_users_client):
    user_list = []
    request = gws_users_client.list(customer='my_customer', maxResults=500)
    while request is not None:
        response = request.execute()
        user_list.extend(response.get('users', []))
        request = gws_users_client.list_next(request, response)

    return dict((u['primaryEmail'].split('@')[0], u) for u in user_list)


def is_enabled_in_kc(attrs):
    return (attrs.get('attributes', {}).get('loginShell') != '/sbin/nologin'
            and attrs['enabled'])


async def process(gws_users_client, keycloak_client=None, dryrun=False):
    kc_users = await list_users(rest_client=keycloak_client)
    gws_users = get_gws_users(gws_users_client)

    # Create missing accounts. Exclude accounts that are disabled in KeyCloak
    # to avoid creating many old user accounts and service accounts.
    disabled_kc_usernames = set(u for u,a in kc_users.items() if not is_enabled_in_kc(a))
    for username,attrs in kc_users.items():
        if username not in set(gws_users).union(disabled_kc_usernames):
            body = {'primaryEmail': f'{username}@icecube.wisc.edu',
                    'name': {
                        'givenName': attrs.get('firstName', 'firstName-undefined'),
                        'familyName': attrs.get('lastName', 'lastName-undefined'),},
                    'password': ''.join(random.choices(string.ascii_letters, k=12)),}
            logger.info(f'creating user {username}')
            if not dryrun:
                gws_users_client.insert(body=body).execute()

    # Get updated GWS user list after account creation
    gws_users = get_gws_users(gws_users_client)

    # Activate suspended GWS accounts that are enabled in KeyCloak
    enabled_kc_usernames = set(u for u,a in kc_users.items() if is_enabled_in_kc(a))
    suspended_gws_usernames = set(u for u,a in gws_users.items() if a['suspended'])
    for username in suspended_gws_usernames.intersection(enabled_kc_usernames):
        logger.info(f'activating enabled user {username}')
        if not dryrun:
            gws_users_client.update(userKey=f'{username}@icecube.wisc.edu',
                                    body={'suspended': False}).execute()

    # Suspend GWS accounts disabled in KeyCloak
    active_gws_usernames = set(u for u,a in gws_users.items() if not a['suspended'])
    for username in active_gws_usernames.intersection(disabled_kc_usernames):
        logger.info(f'suspending disabled user {username}')
        if not dryrun:
            gws_users_client.update(userKey=f'{username}@icecube.wisc.edu',
                                    body={'suspended': True}).execute()


def listener(address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']:
            await process(**kwargs)

    args = {
        'routing_key': 'KK.EVENT.ADMIN.#.USER.#',
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
        description='Sync users from KeyCloak to Google Workspace.',
        epilog='Domain-wide delegation must be enabled for the service account. '
               'The delegator principal must have access to the service account '
               'and have "Service Account Token Creator" role.')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--sa-credentials', metavar='PATH', required=True,
                        help='file with service account credentials')
    parser.add_argument('--sa-delegator', metavar='ACCOUNT', required=True,
                        help='principal on whose behalf the service account will act')
    parser.add_argument('--listen', default=False, action='store_true',
                        help='enable persistent RabbitMQ listener')
    parser.add_argument('--listen-address', help='RabbitMQ address, including user/pass')
    parser.add_argument('--listen-exchange', help='RabbitMQ exchange name')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    creds = service_account.Credentials.from_service_account_file(
        args['sa_credentials'], subject=args['sa_delegator'],
        scopes=['https://www.googleapis.com/auth/admin.directory.user'])
    gws_directory = build('admin', 'directory_v1', credentials=creds, cache_discovery=False)
    gws_users_client = gws_directory.users()

    if args['listen']:
        ret = listener(address=args['listen_address'], exchange=args['listen_exchange'],
                       keycloak_client=keycloak_client, gws_users_client=gws_users_client,
                       dryrun=args['dryrun'])
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(gws_users_client, keycloak_client, dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
