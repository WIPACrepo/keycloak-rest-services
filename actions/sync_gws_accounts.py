"""
Syncs user accounts from KeyCloak to Google Workspace.

Creates missing accounts, suspends and activates accounts as needed.

Example::

    python actions/sync_gws_accounts.py

This will sync all user accounts from KeyCloak to Google Workspace.
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


logger = logging.getLogger('sync_gws_accounts')


def get_gws_accounts(gws_users_client):
    """Return a dictionary with all Google Workspace user accounts"""
    user_list = []
    request = gws_users_client.list(customer='my_customer', maxResults=500)
    while request is not None:
        response = request.execute()
        user_list.extend(response.get('users', []))
        request = gws_users_client.list_next(request, response)

    return dict((u['primaryEmail'].split('@')[0], u) for u in user_list)


def is_eligible(account_attrs):
    """Return True if the account is eligible for creation in Google Workspace."""
    shell = account_attrs.get('attributes', {}).get('loginShell')
    return (account_attrs['enabled'] and shell not in ('/sbin/nologin', None))


def create_missing_eligible_accounts(gws_users_client, gws_accounts, kc_accounts, dryrun):
    """Create eligible KeyCloak accounts in Google Workspace if not there already.

    Google's documentation on account creation, inluding JSON request content:
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users
    """
    created_usernames = []
    for username,attrs in kc_accounts.items():
        if username not in gws_accounts and is_eligible(attrs):
            body = {'primaryEmail': f'{username}@icecube.wisc.edu',
                    'name': {
                        'givenName': attrs.get('firstName', 'firstName-undefined'),
                        'familyName': attrs.get('lastName', 'lastName-undefined'),},
                    'password': ''.join(random.choices(string.ascii_letters, k=12)),}
            created_usernames.append(username)
            logger.info(f'creating user {username}')
            if not dryrun:
                gws_users_client.insert(body=body).execute()
    return created_usernames


def activate_suspended_eligible_accounts(gws_users_client, gws_accounts, kc_accounts, dryrun):
    """Activate suspended GWS accounts if they are (became) "eligible" in KeyCloak"""
    suspended_gws_usernames = set(u for u,a in gws_accounts.items() if a['suspended'])
    eligible_kc_usernames = set(u for u,a in kc_accounts.items() if is_eligible(a))
    activated_usernames = []
    for username in suspended_gws_usernames.intersection(eligible_kc_usernames):
        activated_usernames.append(username)
        logger.info(f'activating enabled user {username}')
        if not dryrun:
            gws_users_client.update(userKey=f'{username}@icecube.wisc.edu',
                                    body={'suspended': False}).execute()
    return activated_usernames


def suspend_active_ineligible_accounts(gws_users_client, gws_accounts, kc_accounts, dryrun):
    """Suspend active GWS accounts if they are (became) "ineligible" in KeyCloak"""
    ineligible_kc_usernames = set(u for u,a in kc_accounts.items() if not is_eligible(a))
    active_gws_usernames = set(u for u,a in gws_accounts.items() if not a['suspended'])
    suspended_usernames = []
    for username in active_gws_usernames.intersection(ineligible_kc_usernames):
        suspended_usernames.append(username)
        logger.info(f'suspending disabled user {username}')
        if not dryrun:
            gws_users_client.update(userKey=f'{username}@icecube.wisc.edu',
                                    body={'suspended': True}).execute()
    return suspended_usernames


async def process(gws_users_client, keycloak_client=None, dryrun=False):
    kc_accounts = await list_users(rest_client=keycloak_client)
    gws_accounts = get_gws_accounts(gws_users_client)

    create_missing_eligible_accounts(gws_users_client, gws_accounts, kc_accounts, dryrun)
    activate_suspended_eligible_accounts(gws_users_client, gws_accounts, kc_accounts, dryrun)
    suspend_active_ineligible_accounts(gws_users_client, gws_accounts, kc_accounts, dryrun)


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
