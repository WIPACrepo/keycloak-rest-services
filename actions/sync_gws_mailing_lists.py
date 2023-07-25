"""
Synchronize memberships of Google Workspace groups to their corresponding
Keycloak mailing list groups. Users are subscribed to Google Workspace groups
using their KeyCloak `canonical_email` attribute.

Only group members whose role is 'MANAGER' or 'MEMBER' are managed. Nothing
is done with the 'OWNER' members (it's assumed these are managed out of band).

Keycloak mailing list groups are the subgroups of /mail. Each group must
have attribute `email` that will be used to map it to a Google Workspace
group.

KeyCloak client can be configured using environment variables. See krs/token.py
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


class GroupDoesNotExist(Exception):
    pass


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


async def get_kc_group_canonical_emails(group_path, keycloak_client):
    """Return a list of canonical emails of members of a KeyCloak group."""
    try:
        usernames = await get_group_membership(group_path, rest_client=keycloak_client)
    except Exception as e:
        if 'does not exist' in e.args[0]:
            raise GroupDoesNotExist
        else:
            raise
    users = [await user_info(u, rest_client=keycloak_client) for u in usernames]
    emails = [u['attributes']['canonical_email'] for u in users]
    return emails


def sync_gws_group_role(group_email, role, role_emails, gws_members_client, dryrun):
    """Sync Google Workspace group members of the given role to the given email list """
    group_members = get_gws_group_members(group_email, gws_members_client)
    initial_this_role_emails = {m['email'] for m in group_members if m['role'] == role}
    initial_other_roles_emails = {m['email'] for m in group_members if m['role'] != role}
    for email in role_emails:
        if email in initial_this_role_emails:
            continue
        body = {'email': email, 'role': role}
        if email in initial_other_roles_emails:
            logger.info(f"Changing {email}'s role in {group_email} to {role} (dryrun={dryrun})")
            if not dryrun:
                gws_members_client.patch(groupKey=group_email, memberKey=email, body=body).execute()
        else:
            logger.info(f"Adding {email} to {group_email} as {role} (dryrun={dryrun})")
            if not dryrun:
                gws_members_client.insert(groupKey=group_email, body=body).execute()

    for email in initial_this_role_emails - set(role_emails):
        logger.info(f"Removing {email} from {group_email} (dryrun={dryrun})")
        if not dryrun:
            gws_members_client.delete(groupKey=group_email, memberKey=email).execute()


async def sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak, dryrun=False):
    """Synchronize memberships of Google Workspace groups to their corresponding
    Keycloak mailing list groups.

    Note that only group members whose role is 'MANAGER' or 'MEMBER' are managed.
    Nothing is done with the 'OWNER' members (it's assumed these are managed out
    ouf band).

    Keycloak mailing list groups are the subgroups of /mail. Each group must
    have attribute `email` that will be used to map it to a Google Workspace
    group.

    Args:
        gws_members_client (googleapiclient.discovery.Resource): Directory API's Members resource
        gws_groups_client (googleapiclient.discovery.Resource): Directory API's Groups resource
        keycloak (OpenIDRestClient): REST client to the KeyCloak server
        dryrun (bool): perform a mock run with no changes made
    """
    res = gws_groups_client.list(customer='my_customer').execute()
    gws_group_emails = [g['email'] for g in res.get('groups', [])]

    kc_ml_root_group = await group_info('/mail', rest_client=keycloak)
    kc_ml_groups = [sg for sg in kc_ml_root_group['subGroups'] if sg['name'] != '_admin']
    for ml_group in kc_ml_groups:
        if 'email' not in ml_group['attributes']:
            logger.error(f"Group {ml_group['path']} doesn't have attribute 'email'. Skipping.")
            continue
        group_email = ml_group['attributes']['email']
        if not group_email:
            logger.error(f"Group {ml_group['path']}'s 'email' attribute is empty. Skipping.")
            continue
        if group_email not in gws_group_emails:
            logger.error(f"Group {group_email} doesn't exist in Google Workspace. Skipping.")
            continue

        try:
            kc_admin_emails = await get_kc_group_canonical_emails(ml_group['path'] + '/_admin', keycloak)
        except GroupDoesNotExist:
            logger.warning(f"Group {ml_group['path']} doesn't have '_admin' subgroup.")
            kc_admin_emails = []
        sync_gws_group_role(group_email, 'MANAGER', kc_admin_emails, gws_members_client, dryrun)

        kc_member_emails = await get_kc_group_canonical_emails(ml_group['path'], keycloak)
        # A user may be a member of both the group and its _admin subgroup.
        # If that's the case, we don't want to overwrite them.
        kc_member_emails = set(kc_member_emails) - set(kc_admin_emails)
        sync_gws_group_role(group_email, 'MEMBER', kc_member_emails, gws_members_client, dryrun)


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
    gws_groups_client = gws_directory.groups()

    asyncio.run(sync_gws_mailing_lists(gws_members_client, gws_groups_client,
                                       keycloak_client, dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
