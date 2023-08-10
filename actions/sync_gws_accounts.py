"""
Sync eligible user accounts from KeyCloak to Google Workspace.
See is_eligible() for how eligibility is determined.

Example::

    python -m actions.sync_gws_accounts --sa-delegator admin-user@icecube.wisc.edu \
                        --sa-credentials keycloak-directory-sync.json

This will sync eligible user accounts from KeyCloak to Google Workspace.
"""
import asyncio
import logging
import random
import string
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from krs.ldap import LDAP
from krs.rabbitmq import RabbitMQListener
from krs.token import get_rest_client
from krs.users import list_users


logger = logging.getLogger('sync_gws_accounts')
SHADOWEXPIRE_DAYS_REMAINING_CUTOFF_FOR_ELIGIBILITY = -365 * 2


def get_gws_accounts(gws_users_client):
    """Return a dictionary with all Google Workspace user accounts.

    Args:
        gws_users_client (googleapiclient.discovery.Resource): Admin API Users resource

    Returns:
        Dict of Google Workspace account attributes keyed by username (not email).
    """
    user_list = []
    request = gws_users_client.list(customer='my_customer', maxResults=500)
    while request is not None:
        response = request.execute()
        user_list.extend(response.get('users', []))
        request = gws_users_client.list_next(request, response)
    return dict((u['primaryEmail'].split('@')[0], u) for u in user_list)


def is_eligible(account_attrs, shadow_expire):
    """Return True if the account is eligible for creation in Google Workspace.

    Args:
        account_attrs (dict): KeyCloak attributes of the account
        shadow_expire (float): value of shadowExpire LDAP attributes of the account

    Return:
        Whether or not the account is eligible for creation
    """
    today = int(time.time()/3600/24)
    days_remaining = shadow_expire - today
    old_account = days_remaining <= SHADOWEXPIRE_DAYS_REMAINING_CUTOFF_FOR_ELIGIBILITY
    shell = account_attrs.get('attributes', {}).get('loginShell')
    return (not old_account
            and account_attrs['enabled']
            and shell not in ('/sbin/nologin', None)
            and account_attrs.get('firstName') and account_attrs.get('lastName'))


def create_missing_eligible_accounts(gws_users_client, gws_accounts, ldap_accounts,
                                     kc_accounts, dryrun):
    """Create eligible KeyCloak accounts in Google Workspace if not there already.

    When creating a new account, also create an email alias if keycloak attributes
    contain 'canonical_email'.
    Google's documentation on account creation:
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users
    API reference for the User resource, including field descriptions:
    https://developers.google.com/admin-sdk/directory/reference/rest/v1/users

    Args:
        gws_users_client (googleapiclient.discovery.Resource): Admin API Users resource
        gws_accounts (dict): GWS account attributes keyed by username
        ldap_accounts (dict): LDAP accounts attributes keyed by username
        kc_accounts (dict): KeyCloak account attributes keyed by username
        dryrun (bool): perform a trial run with no changes made

    Returns:
        List of created usernames (used for unit testing)
    """
    created_usernames = []  # used for unit testing
    for username,attrs in kc_accounts.items():
        shadow_expire = ldap_accounts[username].get('shadowExpire', float('-inf'))
        if username not in gws_accounts and is_eligible(attrs, shadow_expire):
            logger.info(f'creating user {username} (dryrun={dryrun})')
            if dryrun:
                continue
            user_body = {'primaryEmail': f'{username}@icecube.wisc.edu',
                         'name': {
                             'givenName': attrs['firstName'],
                             'familyName': attrs['lastName'],},
                         'password': ''.join(random.choices(string.ascii_letters, k=12)),}
            gws_users_client.insert(body=user_body).execute()
            created_usernames.append(username)
            if 'canonical_email' in attrs['attributes']:
                logger.info(f'inserting alias {attrs["attributes"]["canonical_email"]}')
                for attempt in range(1, 8):
                    time.sleep(2 ** attempt)
                    try:
                        gws_users_client.aliases().insert(
                            userKey=user_body['primaryEmail'],
                            body={'alias': attrs['attributes']['canonical_email']}).execute()
                        break
                    except HttpError as e:
                        if e.status_code == 412:  # precondition failed (user creation not complete?)
                            logger.warning(f'attempt {attempt} to insert alias failed')
                            logger.warning(dir(e))
                            logger.warning(e)
                            continue
                        else:
                            raise
                else:
                    logger.error(f'giving up on alias creation after {attempt} attempts')
        else:
            logger.debug(f'ignoring user {username}')
    return created_usernames


async def process(gws_users_client, ldap_client, keycloak_client, dryrun=False):
    kc_accounts = await list_users(rest_client=keycloak_client)
    gws_accounts = get_gws_accounts(gws_users_client)
    ldap_accounts = ldap_client.list_users(attrs=['shadowExpire'])

    create_missing_eligible_accounts(gws_users_client, gws_accounts, ldap_accounts,
                                     kc_accounts, dryrun)


def listener(address=None, exchange=None, dedup=1, **kwargs):
    """Set up RabbitMQ listener"""
    async def action(message):
        logger.debug(f'{message}')
        if message['representation']:
            await process(**kwargs)

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

    parser = argparse.ArgumentParser(
        description='Sync eligible user accounts from KeyCloak to Google Workspace. '
                    'Eligibility is determined by the is_eligible() function.',
        epilog='Notes: (1) LDAP and KeyCloak clients are configured using environment '
               'variables. See krs/ldap.py and krs/token.py for details. '
               '(2): Domain-wide delegation must be enabled for the service account. '
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
    ldap_client = LDAP()

    creds = service_account.Credentials.from_service_account_file(
        args['sa_credentials'], subject=args['sa_delegator'],
        scopes=['https://www.googleapis.com/auth/admin.directory.user',
                'https://www.googleapis.com/auth/admin.directory.user.alias'])
    gws_directory = build('admin', 'directory_v1', credentials=creds, cache_discovery=False)
    gws_users_client = gws_directory.users()

    if args['listen']:
        ret = listener(address=args['listen_address'], exchange=args['listen_exchange'],
                       keycloak_client=keycloak_client, gws_users_client=gws_users_client,
                       ldap_client=ldap_client, dryrun=args['dryrun'])
        loop = asyncio.get_event_loop()
        loop.create_task(ret.start())
        loop.run_forever()
    else:
        asyncio.run(process(gws_users_client, ldap_client, keycloak_client, dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
