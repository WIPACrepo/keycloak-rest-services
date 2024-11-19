"""
Send emails about password expiration.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import logging
from pprint import pprint
import time

from krs.token import get_rest_client
from krs.email import send_email
from krs.ldap import LDAP
from krs.users import modify_user


logger = logging.getLogger('ldap_password_exp_email')


EXPIRING_MSG = '''All IceCube passwords expire after six months and the six month
expiration date for your current password is rapidly approaching.

According to our records, your username and password expiration
date are:

   Username:         {uid}
   Expiration Date:  {date:%Y-%m-%d}

After your password expires, you will no longer be able to retrieve
your e-mail, login to IceCube computing systems, or use many other
IceCube resources.

Please go to https://keycloak.icecube.wisc.edu/auth/realms/IceCube/account/#/account-security/signing-in
where you can update your password.
'''


EXPIRED_MSG = '''All IceCube passwords expire after six months and the six month
expiration date for your current password has passed.

According to our records, your username {uid} has expired.

You will no longer be able to retrieve your e-mail, login to
IceCube computing systems, or use many other IceCube resources.

Please go to https://keycloak.icecube.wisc.edu/auth/realms/IceCube/account
where you can reset your password.
'''


async def _get_expired_users(ldap_users, usernames):
    today = int(time.time()/3600/24)
    now = datetime.now(timezone.utc)

    expiring_users = {}
    expired_users = {}
    disabled_users = {}

    for uid in sorted(usernames):
        user = ldap_users[uid]
        logger.debug('processing user %s', uid)
        if user.get('shadowExpire', 0) > 0 and user.get('shadowMax', 0) > 0:

            days_remaining = int(user['shadowExpire']) - today
            logger.debug('user %s has %d days remaining', uid, days_remaining)
            exp_date = (now + timedelta(days=days_remaining)).date()

            if days_remaining < -180:
                disabled_users[uid] = exp_date
            elif -7 < days_remaining <= 0:
                expired_users[uid] = exp_date
            elif 0 < days_remaining <= 28:
                expiring_users[uid] = exp_date

    return expiring_users, expired_users, disabled_users


async def process(username=None, dryrun=False, ldap_client=None, keycloak_client=None):
    ldap_users = ldap_client.list_users()

    if username:
        usernames = [username]
    else:
        usernames = list(ldap_users)

    expiring_users, expired_users, disabled_users = await _get_expired_users(ldap_users, usernames)

    if dryrun:
        print('expiring users')
        pprint(expiring_users)
        print('\nexpired users')
        pprint(expired_users)
        print('\ndisabled users')
        pprint(disabled_users)

    # send out expiring emails
    for uid in expiring_users:
        try:
            user = ldap_users[uid]
            name = user.get('givenName', uid)
            email_addr = user.get('mail', '')
            msg = EXPIRING_MSG.format(uid=uid, date=expiring_users[uid])
            if email_addr:
                if dryrun:
                    print(msg)
                else:
                    send_email({'name': name, 'email': email_addr}, 'IceCube Password Expiring', msg)
        except Exception:
            logger.warning(f'error sending expiring email to {uid}', exc_info=True)

    for uid in expired_users:
        # make sure Keycloak knows about expirations
        if not dryrun:
            try:
                await modify_user(uid, actions=['UPDATE_PASSWORD'], rest_client=keycloak_client)
            except Exception:
                logger.warning(f'error updating keycloak with expired password for {uid}', exc_info=True)

        # send out expired emails
        try:
            user = ldap_users[uid]
            name = user.get('givenName', uid)
            email_addr = user.get('mail', '')
            msg = EXPIRED_MSG.format(uid=uid)
            if email_addr:
                if dryrun:
                    print(msg)
                else:
                    send_email({'name': name, 'email': email_addr}, 'IceCube Password Has Expired', msg)
        except Exception:
            logger.warning(f'error sending expired email to {uid}', exc_info=True)

    # send out admin emails
    try:
        msg = 'The following accounts will expire in the next 28 days.\n\n'
        msg += '{:16} Date Account Expires\n'.format('Username')
        msg += '---------------- --------------------\n'
        for uid in expiring_users:
            msg += f'{uid:16} {expiring_users[uid]:%Y-%m-%d}\n'
        if dryrun:
            print(msg)
        else:
            send_email({'name': 'IceCube Admin Team', 'email': 'admin@icecube.wisc.edu'}, 'Accounts Expiring Soon', msg)
    except Exception:
        logger.warning('error sending admin expiring email', exc_info=True)

    try:
        msg = 'The following accounts have expired.\n\n'
        msg += '{:16} Date Account Expired\n'.format('Username')
        msg += '---------------- --------------------\n'
        for uid in expired_users:
            msg += f'{uid:16} {expired_users[uid]:%Y-%m-%d}\n'
        if dryrun:
            print(msg)
        else:
            send_email({'name': 'IceCube Admin Team', 'email': 'admin@icecube.wisc.edu'}, 'Expired Accounts', msg)
    except Exception:
        logger.warning('error sending admin expired email', exc_info=True)

    return  # ignore disabled users for now
    try:
        msg = 'The following accounts are disabled.\n\n'
        for uid in disabled_users:
            msg += uid + '\n'
        if dryrun:
            print(msg)
        else:
            send_email({'name': 'IceCube Admin Team', 'email': 'admin@icecube.wisc.edu'}, 'Disabled Accounts', msg)
    except Exception:
        logger.warning('error sending admin disabled email', exc_info=True)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update user shadowExpire in LDAP')
    parser.add_argument('--user', default=None, help='process a single user')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    ldap_client = LDAP()
    keycloak_client = get_rest_client()

    asyncio.run(process(args['user'], dryrun=args['dryrun'], ldap_client=ldap_client, keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
