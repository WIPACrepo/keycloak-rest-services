"""
Synchronize memberships of Google Workspace groups to their corresponding
Keycloak mailing list groups. Users are subscribed to Google Workspace groups
using their KeyCloak `canonical_email` attribute, unless it is overridden
by `mailing_list_email` (unless it's an @icecube.wisc.edu address, in which
case it's ignored).

Users can optionally be notified of changes via email. SMTP server is
controlled by the EMAIL_SMTP_SERVER environmental variable and defaults
to localhost. See krs/email.py for more email options.

Only group members whose role is 'MANAGER' or 'MEMBER' are managed. Nothing
is done with the 'OWNER' members (it's assumed these are managed out of band).

Keycloak mailing list groups are the subgroups of /mail. Each group must
have attribute `email` that will be used to map it to a Google Workspace
group.

KeyCloak REST client is configured using environment variables. See
krs/token.py for details.

Domain-wide delegation must be enabled for the Google Workspace service
account. See code for which scopes are required. Admin API must be enabled
in the Google Cloud Console project.

The delegate principal must have Google Workspace admin role, be accessible
to the service account (in Google Cloud project under IAM), and have
"Service Account Token Creator" role (in Google Cloud project under IAM).
"""
import asyncio
import logging

from asyncache import cached
from cachetools import Cache

from googleapiclient.discovery import build
from google.oauth2 import service_account

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, GroupDoesNotExist
from krs.users import user_info
from krs.email import send_email

logger = logging.getLogger('sync_gws_mailing_lists')

MESSAGE_FOOTER = "\n\nThis message was generated by the sync_gws_mailing_lists robot."

SUBSCRIPTION_MESSAGE = "You have been subscribed to {group_email} mailing list as {email} "\
                       "with role {role} and delivery option {delivery} because you " \
                       "are a member of group {group_path} or {group_path}/_admin.\n\n" \
                       "Note: delivery option NONE is usually used for IceCube addresses " \
                       "of individuals who subscribe to mailing lists with non-IceCube emails. " \
                       "This allows using https://groups.google.com with the IceCube account " \
                       "without receiving duplicate emails." \
                       + MESSAGE_FOOTER

ROLE_CHANGE_MESSAGE = "The role of {email} in {group_email} has changed to {role} because " \
                      "of membership change involving {group_path} and {group_path}/_admin." \
                      + MESSAGE_FOOTER

UNSUBSCRIPTION_MESSAGE = "{email} has been unsubscribed from {group_email} mailing list " \
                         "because you are no longer a member of either {group_path} or " \
                         "{group_path}/_admin." + MESSAGE_FOOTER


@cached(Cache(maxsize=2500))
async def cached_user_info(username, rest_client):
    return await user_info(username, rest_client=rest_client)


def get_gws_group_members(group_email, gws_members_client) -> list:
    """Return a list of Google Workspace group member dicts.

    Specification of group member dictionary is here:
    https://developers.google.com/admin-sdk/directory/reference/rest/v1/members#Member

    Args:
        group_email (str): Google Workspace group email
        gws_members_client (googleapiclient.discovery.Resource): Admin API Members resource

    Returns:
        list: list of member dicts
    """
    ret = []
    req = gws_members_client.list(groupKey=group_email)
    while req is not None:
        res = req.execute()
        if 'members' in res:
            ret.extend(res['members'])
        req = gws_members_client.list_next(req, res)
    return ret


async def get_gws_members_from_keycloak_group(group_path, role, keycloak_client) -> dict:
    """Return a dict of GWS group member object dicts based on member emails of the keycloak group"""
    ret = {}
    usernames = await get_group_membership(group_path, rest_client=keycloak_client)
    # noinspection PyCallingNonCallable
    users = [await cached_user_info(u, keycloak_client) for u in usernames]
    for user in users:
        canonical = user['attributes']['canonical_email']
        preferred = user['attributes'].get('mailing_list_email')
        if isinstance(preferred, str) and preferred.endswith('@icecube.wisc.edu'):
            # User mistakenly configured mailing_list_email to be an @icecube.wisc.edu
            # address. This doesn't make sense and is not allowed.
            preferred = None
        if preferred:
            # If a user has a preferred mailing list email, also add their canonical
            # (IceCube) email as a no-mail member, since they may not be able to log
            # on to groups.google.com with the preferred address (to see archives, etc.)
            ret[preferred] = {'email': preferred, 'delivery_settings': 'ALL_MAIL', 'role': role}
            ret[canonical] = {'email': canonical, 'delivery_settings': 'NONE', 'role': role}
        else:
            ret[canonical] = {'email': canonical, 'delivery_settings': 'ALL_MAIL', 'role': role}
    return ret


async def sync_kc_group_to_gws(kc_group, group_email, keycloak_client, gws_members_client,
                               send_notifications, dryrun):
    """
    Sync a single KeyCloak mailing group to Google Workspace Group.

    Note that only group members whose role is 'MANAGER' or 'MEMBER' are managed.
    Nothing is done with the 'OWNER' members (it's assumed these are managed out
    ouf band).
    """
    try:
        managers = await get_gws_members_from_keycloak_group(
            kc_group['path'] + '/_admin', 'MANAGER', keycloak_client)
    except GroupDoesNotExist:
        managers = {}
    members = await get_gws_members_from_keycloak_group(
        kc_group['path'], 'MEMBER', keycloak_client)
    # A user may be a member of both the mailing list group and its _admin subgroup.
    # If that's the case, we want to use their manager settings.
    target_membership = members | managers
    actual_membership = {member['email']: {'email': member['email'], 'role': member['role']}
                         for member in get_gws_group_members(group_email, gws_members_client)}

    for email, body in target_membership.items():
        if email not in actual_membership:
            logger.info(f"Inserting into {group_email} {body} (dryrun={dryrun})")
            if not dryrun:
                gws_members_client.insert(groupKey=group_email, body=body).execute()
                if send_notifications:
                    send_email(email, f"You have been subscribed to {group_email}",
                               SUBSCRIPTION_MESSAGE.format(
                                   group_email=group_email,
                                   email=email,
                                   role=body['role'],
                                   delivery=body['delivery_settings'],
                                   group_path=kc_group['path']),
                               headline='IceCube Mailing List Management')
        # if email already subscribed
        elif body['role'] != actual_membership[email]['role']:
            logger.info(f"Patching in {group_email} role of {email} to {body['role']} (dryrun={dryrun})")
            if not dryrun:
                gws_members_client.patch(groupKey=group_email, memberKey=email,
                                         body={'email': email, 'role': body['role']}).execute()
                if send_notifications:
                    send_email(email, f"Your member role in {group_email} has changed",
                               ROLE_CHANGE_MESSAGE.format(
                                   group_email=group_email,
                                   email=email,
                                   role=body['role'],
                                   group_path=kc_group['path']),
                               headline='IceCube Mailing List Management')

    for email in set(actual_membership) - set(target_membership):
        if actual_membership[email]['role'] != 'OWNER':
            logger.info(f"Removing from {group_email} {email} (dryrun={dryrun})")
            if not dryrun:
                gws_members_client.delete(groupKey=group_email, memberKey=email).execute()
                if send_notifications:
                    send_email(email, f"You have been unsubscribed from {group_email}",
                               UNSUBSCRIPTION_MESSAGE.format(
                                   group_email=group_email,
                                   email=email,
                                   role=actual_membership[email]['role'],
                                   group_path=kc_group['path']),
                               headline='IceCube Mailing List Management')


async def sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_client,
                                 single_group=None, send_notifications=True, dryrun=False):
    """Synchronize memberships of Google Workspace groups to their corresponding
    Keycloak mailing list groups, and optionally notify users of changes.

    Note that only group members whose role is 'MANAGER' or 'MEMBER' are managed.
    Nothing is done with the 'OWNER' members (it's assumed these are managed out
    ouf band).

    Keycloak mailing list groups are the subgroups of /mail. Each group must
    have attribute `email` that will be used to map it to a Google Workspace
    group.

    Args:
        gws_members_client (googleapiclient.discovery.Resource): Directory API's Members resource
        gws_groups_client (googleapiclient.discovery.Resource): Directory API's Groups resource
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        single_group (str): only consider this group instead of all groups
        send_notifications (bool): whether to send email notifications
        dryrun (bool): Perform a mock run with no changes made
    """
    res = gws_groups_client.list(customer='my_customer').execute()
    gws_group_emails = [g['email'] for g in res.get('groups', [])]

    kc_ml_root_group = await group_info('/mail', rest_client=keycloak_client)
    if single_group:
        logger.warning(f"Only group {single_group} will be considered.")
        kc_ml_groups = [sg for sg in kc_ml_root_group['subGroups'] if sg['name'] == single_group]
    else:
        kc_ml_groups = [sg for sg in kc_ml_root_group['subGroups'] if sg['name'] != '_admin']
    for ml_group in kc_ml_groups:
        if not ml_group['attributes'].get('email'):
            logger.warning(f"Attribute 'email' of {ml_group['path']} is missing or empty'. Skipping.")
            continue
        group_email = ml_group['attributes']['email']
        if group_email not in gws_group_emails:
            logger.error(f"Group '{group_email}' doesn't exist in Google Workspace. Skipping.")
            continue

        await sync_kc_group_to_gws(ml_group, group_email, keycloak_client, gws_members_client,
                                   send_notifications, dryrun)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Synchronize memberships of Google Workspace groups to their '
                    'corresponding Keycloak mailing list groups. Optionally, '
                    'notify users of changes.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='See module docstring for details, including SMTP server configuration.')
    parser.add_argument('--sa-credentials', metavar='PATH', required=True,
                        help='file with service account credentials')
    parser.add_argument('--sa-delegator', metavar='ACCOUNT', required=True,
                        help='principal on whose behalf the service account will act')
    parser.add_argument('--send-notifications', action='store_true',
                        help='send email notifications to users')
    parser.add_argument('--single-group', metavar='NAME',
                        help='only consider group NAME')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--dryrun', action='store_true', help='dry run')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    creds = service_account.Credentials.from_service_account_file(
        args['sa_credentials'], subject=args['sa_delegator'],
        scopes=['https://www.googleapis.com/auth/admin.directory.group.member',
                'https://www.googleapis.com/auth/admin.directory.group'])
    gws_directory = build('admin', 'directory_v1', credentials=creds, cache_discovery=False)
    gws_members_client = gws_directory.members()
    gws_groups_client = gws_directory.groups()

    asyncio.run(sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_client,
                                       args['single_group'], args['send_notifications'],
                                       dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
