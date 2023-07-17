"""
Synchronize memberships of Google Workspace groups to their corresponding
Keycloak mailing list groups. Users are subscribed to Google Workspace groups
using their KeyCloak `canonical_email` attribute.

Keycloak mailing list groups are the subgroups of /mail. Each group must
have attribute `email` that will be used to map it to a Google Workspace
group.

KeyCloak client is configured using environment variables. See krs/token.py
for details.

Domain-wide delegation must be enabled for the service account. See code
for which scopes are required. Admin API must be enabled in the Google
Cloud Console project.

The delegator principal must have the Google Workspace admin role, have
access to the service account, and have "Service Account Token Creator"
role.
"""
import asyncio
import logging

from googleapiclient.discovery import build
from google.oauth2 import service_account

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info
from krs.users import user_info


logger = logging.getLogger('sync_gws_mailing_lists')


def get_all_group_members(group_email, gws_members_client):
    """Get email addresses of all members of a Google Workspace members"""
    req = gws_members_client.list(groupKey=group_email)
    members = []
    while req is not None:
        res = req.execute()
        if 'members' in res:
            members.extend(m['email'] for m in res['members'])
        else:
            break
        req = gws_members_client.list_next(req, res)
    return members


async def sync_gws_mailing_lists(gws_members_client, keycloak_client, dryrun=False):
    """Synchronize memberships of Google Workspace groups to their corresponding
    Keycloak mailing list groups.

    Keycloak mailing list groups are the subgroups of /mail. Each group must
    have attribute `email` that will be used to map it to a Google Workspace
    group.

    Args:
        gws_members_client (googleapiclient.discovery.Resource): Directory API's Members resource
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server

    Returns:
        dict: run summary for unit tests
    """
    debug = {"added": set(), "deleted": set()}
    ml_root_group = await group_info('/mail', keycloak_client)
    ml_groups = [sg for sg in ml_root_group['subGroups'] if sg['name'] != '_admin']
    for ml_group in ml_groups:
        if 'email' not in ml_group['attributes']:
            logger.error(f"Group {ml_group['path']} doesn't have attribute 'email'")
            continue
        group_email = ml_group['attributes']['email'][0]
        kc_usernames = await get_group_membership(ml_group['path'], rest_client=keycloak_client)
        kc_users = [await user_info(u, rest_client=keycloak_client) for u in kc_usernames]
        kc_emails = [u['attributes']['canonical_email'] for u in kc_users]
        gws_emails = get_all_group_members(group_email, gws_members_client)

        missing_emails = set(kc_emails) - set(gws_emails)
        for email in missing_emails:
            logger.info(f"Adding {email} to {group_email} (dryrun={dryrun})")
            debug["added"].add(email)
            if not dryrun:
                gws_members_client.insert(groupKey=group_email, body={'email': email}).execute()

        unwanted_emails = set(gws_emails) - set(kc_emails)
        for email in unwanted_emails:
            logger.info(f"Deleting {email} from {group_email} (dryrun={dryrun})")
            debug["deleted"].add(email)
            if not dryrun:
                gws_members_client.delete(groupKey=group_email, memberKey=email).execute()
    return debug


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Synchronize memberships of Google Workspace groups to their '
                    'corresponding Keycloak mailing list groups.',
        epilog='See module docstring for details.')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('--sa-credentials', metavar='PATH', required=True,
                        help='file with service account credentials')
    parser.add_argument('--sa-delegator', metavar='ACCOUNT', required=True,
                        help='principal on whose behalf the service account will act')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    creds = service_account.Credentials.from_service_account_file(
        args['sa_credentials'], subject=args['sa_delegator'],
        scopes=['https://www.googleapis.com/auth/admin.directory.group.member',
                'https://www.googleapis.com/auth/admin.directory.group'])
    gws_directory = build('admin', 'directory_v1', credentials=creds, cache_discovery=False)
    gws_members_client = gws_directory.members()

    asyncio.run(sync_gws_mailing_lists(gws_members_client, keycloak_client, dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
