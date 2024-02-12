"""
Sync eligible user accounts from KeyCloak to Google Workspace and apply
standard configuration to them.
See is_eligible() for how eligibility is determined.

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::

    python -m actions.sync_gws_accounts --sa-subject admin-user@icecube.wisc.edu \
                        --sa-credentials keycloak-directory-sync.json

This will sync eligible user accounts from KeyCloak to Google Workspace.
"""
import asyncio
import logging
import random
import string
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build

from krs.ldap import LDAP
from krs.token import get_rest_client
from krs.users import list_users

from actions.util import retry_execute

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
        response = retry_execute(request)
        user_list.extend(response.get('users', []))
        request = gws_users_client.list_next(request, response)
    return dict((u['primaryEmail'].split('@')[0], u) for u in user_list)


def add_canonical_alias(gws_users_client, kc_attrs):
    """Add the canonical email address as an alias for the account in kc_attrs.

    Args:
        gws_users_client (googleapiclient.discovery.Resource): Admin API Users resource.
        kc_attrs (dict): KeyCloak dictionary of the user being operated on.
    """
    if not kc_attrs.get("attributes", {}).get("canonical_email"):
        logger.error(f'can\'t set canonical alias because user {kc_attrs["username"]} '
                     f'doesn\'t have attribute canonical_email')
        return
    logger.info(f'adding to {kc_attrs["username"]} alias {kc_attrs["attributes"]["canonical_email"]}')
    retry_execute(gws_users_client.aliases().insert(
        userKey=f'{kc_attrs["username"]}@icecube.wisc.edu',
        body={'alias': kc_attrs["attributes"]["canonical_email"]}))


def set_canonical_sendas(gws_creds, kc_attrs):
    """Set gmail sendAs address of the account described by kc_attrs to its canonical email.

    For this to work, gmail has to be enabled for the user and the canonical email needs
    to be configured as an alias for the user.

    Args:
        gws_creds: Google API credentials
        kc_attrs (dict): KeyCloak dictionary of the user being operated on.
    """
    if not kc_attrs.get("attributes", {}).get("canonical_email"):
        logger.error(f'can\'t set canonical sendAs because user {kc_attrs["username"]} '
                     f'doesn\'t have attribute canonical_email')
        return
    logger.info(f'setting sendAs of {kc_attrs["username"]} to {kc_attrs["attributes"]["canonical_email"]}')
    if gws_creds is None:
        return  # we are being unit tested
    creds_delegated = gws_creds.with_subject(f'{kc_attrs["username"]}@icecube.wisc.edu')
    gmail = build('gmail', 'v1', credentials=creds_delegated, cache_discovery=False)
    sendas = gmail.users().settings().sendAs()
    body = {
        "displayName": f"{kc_attrs['firstName']} {kc_attrs['lastName']}",
        "sendAsEmail": kc_attrs["attributes"]["canonical_email"],
        "isDefault": True,
        "treatAsAlias": True,
    }
    retry_execute(sendas.create(userId='me', body=body))


def is_eligible(account_attrs, shadow_expire):
    """Return True if the account is eligible for creation in Google Workspace.

    Args:
        account_attrs (dict): KeyCloak attributes of the account
        shadow_expire (float): value of shadowExpire LDAP attributes of the account

    Return:
        Whether the account is eligible for creation
    """
    today = int(time.time()/3600/24)
    days_remaining = shadow_expire - today
    old_account = days_remaining <= SHADOWEXPIRE_DAYS_REMAINING_CUTOFF_FOR_ELIGIBILITY
    shell = account_attrs.get('attributes', {}).get('loginShell')
    force_creation_in_gws = account_attrs.get('attributes', {}).get('force_creation_in_gws')
    if force_creation_in_gws == 'true':
        force_create = True
    elif force_creation_in_gws is None:
        force_create = False
    else:
        logger.error(f'Attribute force_creation_in_gws of {account_attrs["username"]} is '
                     'defined but not set to "true". This isn\'t allowed. Ignoring user.')
        return False
    return (account_attrs['enabled'] and
            (force_create or (not old_account
                              and shell not in ('/sbin/nologin', None)
                              and account_attrs.get('firstName')
                              and account_attrs.get('lastName'))))


def create_missing_eligible_accounts(gws_users_client, gws_accounts, ldap_accounts,
                                     kc_accounts, gws_creds, dryrun):
    """Create eligible KeyCloak accounts in Google Workspace if not there already.

    When creating a new account, also create an email alias if keycloak attributes
    contain 'canonical_email'.
    Google's documentation on account creation:
    https://developers.google.com/admin-sdk/directory/v1/guides/manage-users
    API reference for the User resource, including field descriptions:
    https://developers.google.com/admin-sdk/directory/reference/rest/v1/users

    Args:
        gws_users_client: Google Admin API Users resource
        gws_accounts (dict): GWS account attributes keyed by username
        ldap_accounts (dict): LDAP accounts attributes keyed by username
        kc_accounts (dict): KeyCloak account attributes keyed by username
        gws_creds: Google API credentials with domain-wide delegation
        dryrun (bool): perform a trial run with no changes made

    Returns:
        List of created usernames (used for unit testing)
    """
    created_usernames = []  # used for unit testing
    for username, attrs in kc_accounts.items():
        shadow_expire = ldap_accounts[username].get('shadowExpire', float('-inf'))
        if username not in gws_accounts and is_eligible(attrs, shadow_expire):
            logger.info(f'creating user {username} (dryrun={dryrun})')
            if dryrun:
                continue
            user_body = {'primaryEmail': f'{username}@icecube.wisc.edu',
                         'name': {
                             'givenName': attrs['firstName'],
                             'familyName': attrs['lastName']},
                         'password': ''.join(random.choices(string.ascii_letters, k=16))}
            retry_execute(gws_users_client.insert(body=user_body))
            time.sleep(3)  # give time to finish user creation before configuring it
            created_usernames.append(username)
            if attrs.get('attributes', {}).get('canonical_email'):
                try:
                    add_canonical_alias(gws_users_client, attrs)
                    time.sleep(3)  # give time to finish alias creation before setting is as sendas
                    set_canonical_sendas(gws_creds, attrs)
                except:  # noqa
                    logger.error(f'Account config failed midway. Canonical alias and/or SendAs of '
                                 f'{username} must be manually set to {attrs["attributes"]["canonical_email"]}')
                    raise
        else:
            logger.debug(f'ignoring existing or ineligible user {username}')
    return created_usernames


async def sync_gws_accounts(gws_users_client, ldap_client, keycloak_client,
                            gws_creds, dryrun=False):
    """This function looks like this to enable unit testing without needing to simulate
    clients for Google API, LDAP, and KeyCloak.
    """
    kc_accounts = await list_users(rest_client=keycloak_client)
    gws_accounts = get_gws_accounts(gws_users_client)
    ldap_accounts = ldap_client.list_users(attrs=['shadowExpire'])  # noqa pycharm bug?

    create_missing_eligible_accounts(gws_users_client, gws_accounts, ldap_accounts,
                                     kc_accounts, gws_creds, dryrun)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Sync eligible user accounts from KeyCloak to Google Workspace and '
                    'configure them. Eligibility is determined by the is_eligible() '
                    'function.',
        epilog='Notes: (1) LDAP and KeyCloak clients are configured using environment '
               'variables. See krs/ldap.py and krs/token.py for details. '
               '(2): Domain-wide delegation must be enabled for the service account. '
               'The account on whose behalf the service account will act must have '
               'have "Service Account Token Creator" role [*not sure*].')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--sa-credentials', metavar='PATH', required=True,
                        help='JSON file with service account credentials')
    parser.add_argument('--sa-subject', metavar='ACCOUNT', required=True,
                        help='principal on whose behalf the service account will act')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    ldap_client = LDAP()

    scopes = ['https://www.googleapis.com/auth/admin.directory.user',  # create user
              'https://www.googleapis.com/auth/admin.directory.user.alias',  # add alias
              'https://www.googleapis.com/auth/gmail.settings.sharing']  # sendas setting
    creds = service_account.Credentials.from_service_account_file(
        args['sa_credentials'], subject=args['sa_subject'], scopes=scopes)
    gws_directory = build('admin', 'directory_v1', credentials=creds, cache_discovery=False)
    gws_users_client = gws_directory.users()

    asyncio.run(sync_gws_accounts(
        gws_users_client=gws_users_client,
        ldap_client=ldap_client,
        keycloak_client=keycloak_client,
        gws_creds=creds,
        dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
