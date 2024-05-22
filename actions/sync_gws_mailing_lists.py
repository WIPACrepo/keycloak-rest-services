"""
Synchronize/update memberships of Google Workspace mailing groups/lists
to match their corresponding Keycloak "mail groups". A Keycloak group is
a " mail group" if and only if it is a direct subgroup of the /mail group.

In order to be operated on by this script, mail groups must define attribute
`email` to match them to the corresponding Google Workspace mailing group/list.

Only Google Workspace group members whose role is 'MANAGER' or 'MEMBER'
are managed. 'OWNER' members should be managed by other means.

Members of all recursive subgroups of a mail groups will be subscribed to the
list. This is to support such use patterns as:
 - A mail group membership is managed by an automated process, but the
    corresponding mailing list needs to have some extra members that the
    process doesn't handle.
 - A subgroup of a mail group is automatically managed, for example when
    policy requires members of one group to also be members of another group.

Members of subgroups called "_admin" and "_managers" will have assigned role
'MANAGER'. The magic group "_managers" is needed to designate managers for groups
that are automatically generated (and therefore can't have an _admin subgroup).

Users are subscribed to Google Workspace groups using their KeyCloak
`canonical_email` attribute, unless it is overridden by `mailing_list_email`.
Use of `canonical_email`, instead of just username@icecube.wisc.edu, is needed
for the *VERY* rare case of the keycloak user not being in Google Workspace.
(In this case, the user would send messages to the list from their canonical
address, as this is what our mail server is configured to do, so that's the
address they must be subscribed to the list with.) Once we stop using our
own mail server, this requirement will become unnecessary. Removing code
that implements this requirement will necessitate some member conversions
but will simplify code.

Users can optionally be notified of changes via email. SMTP server is
controlled by the EMAIL_SMTP_SERVER environmental variable and defaults
to localhost. See send_email() in krs/email.py for more email options.

KeyCloak REST client is typically configured using environment variables.
See krs/token.py for details.

Domain-wide delegation must be enabled for the Google Workspace service
account and appropriate scopes authorized. See code for which scopes are
required. Admin API must be enabled in the Google Cloud Console project.

The admin account on whose behalf the service account will act *may* need to
have "Service Account Token Creator" role (in Google Cloud project under IAM).

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes
PLEASE KEEP THAT PAGE IN-SYNC WITH THIS CODE.
"""
import asyncio
import logging

from asyncache import cached  # type: ignore
from cachetools import Cache
from collections import defaultdict

# noinspection PyProtectedMember
from googleapiclient.discovery import build, Resource  # type: ignore
from google.oauth2 import service_account  # type: ignore

from rest_tools.client import RestClient

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info
from krs.users import user_info, UserDoesNotExist
from krs.email import send_email

from actions.util import retry_execute, group_tree_to_list, reflow_text

ACTION_ID = 'sync_gws_mailing_lists'
logger = logging.getLogger(ACTION_ID)

# Paragraph separator. Used for re-flowing text.
PARA_SEP = "\n\n"

MESSAGE_FOOTER = f"""This message was generated by the {ACTION_ID}
robot. Please contact help@icecube.wisc.edu for support and feedback."""

NONE_EXPLANATION = """Note: delivery mode NONE is used for IceCube
emails of individuals who subscribe to mailing lists with non-IceCube
addresses. This allows using https://groups.google.com with the IceCube
account without receiving duplicate emails."""

SUBSCRIPTION_MESSAGE = ("""You have been subscribed to {group_email} mailing
list as {email} with role {role} and delivery mode {delivery} because you
are a member of group(s) {qualifying_groups}.{none_explanation}"""
                        + PARA_SEP + MESSAGE_FOOTER)

ROLE_CHANGE_MESSAGE = ("""The role of {email} in {group_email} mailing list
has changed from {old_role} to {new_role} because of membership change involving
a managerial subgroup of {group_path}.""" + PARA_SEP + MESSAGE_FOOTER)

UNSUBSCRIPTION_MESSAGE = ("""{email} has been unsubscribed from {group_email}
mailing list because either you are no longer a member of {group_path} and its
subgroups, or you have updated your preferred address for mailing lists."""
                          + PARA_SEP + MESSAGE_FOOTER)


@cached(Cache(maxsize=5000))
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
        res = retry_execute(req)
        if 'members' in res:
            ret.extend(res['members'])
        req = gws_members_client.list_next(req, res)
    return ret


async def get_gws_members_from_kc_group(group_path, role, keycloak_client) -> dict:
    """Return a dict of GWS group member object dicts based on member emails of the
    keycloak group"""
    ret = {}
    usernames = await get_group_membership(group_path, rest_client=keycloak_client)
    # noinspection PyCallingNonCallable
    users = [await cached_user_info(u, keycloak_client) for u in usernames]
    for user in users:
        # See file docstring for the explanation of why we try to use the canonical address.
        canonical = user['attributes'].get('canonical_email')
        if not canonical:
            # There are malformed accounts out there that don't have canonical_email
            canonical = f"{user['username']}@icecube.wisc.edu"
        # Preferred addresses are controlled by users, so sanitize
        preferred = user['attributes'].get('mailing_list_email', '').strip().lower()
        if preferred == canonical:
            # If preferred is the same as canonical, the user misunderstood what
            # mailing_list_email attribute is for, and this can safely be ignored
            preferred = ''

        # If preferred mailing list address is not set (the most common case),
        # subscribe using the canonical address
        if not preferred:
            ret[canonical] = {'email': canonical, 'delivery_settings': 'ALL_MAIL', 'role': role}
        else:
            # if preferred is set, use it
            ret[preferred] = {'email': preferred, 'delivery_settings': 'ALL_MAIL', 'role': role}
            # The preferred address could be username@icecube.wisc.edu (it can't be the
            # canonical address). Although rare, this may not be a mistake. In this case
            # we don't need to do anything special for the user to have access to
            # groups.google.com.
            # If, as in most cases, a user's preferred address mailing list address is
            # not @icecube.wisc.edu, also add their canonical @icecube.wisc.edu email as
            # a no-mail member, since they may not be able to log on to groups.google.com
            # with the preferred address (to see archives, etc.)
            if not preferred.endswith('@icecube.wisc.edu'):
                ret[canonical] = {'email': canonical, 'delivery_settings': 'NONE', 'role': role}
    return ret


async def sync_kc_group_tree_to_gws(kc_root_group: dict, group_email: str, keycloak_client: RestClient,
                                    gws_members_client: Resource, send_notifications: bool, dryrun: bool):
    """
    Sync a single KeyCloak mailing group with subgroups to Google Workspace Group.

    Note that only group members whose role is 'MANAGER' or 'MEMBER' are managed.
    Nothing is done with the 'OWNER' members (it's assumed these are managed out
    ouf band). List of members who ought to be subscribed to the list are determined
    recursively. See file docstring for important information subgroup handling.
    """
    # Determine who should be subscribed to the list and in what role.
    member_kc_groups = defaultdict(list)  # track member's source keycloak group by email
    all_intended_members = {}
    all_intended_managers = {}
    for group in group_tree_to_list(kc_root_group):
        if group['name'] in ('_admin', '_managers'):
            group_members = await get_gws_members_from_kc_group(group['path'], 'MANAGER', keycloak_client)
            all_intended_managers |= group_members
        else:
            group_members = await get_gws_members_from_kc_group(group['path'], 'MEMBER', keycloak_client)
            all_intended_members |= group_members
        for email in group_members:
            member_kc_groups[email].append(group['path'])

    # A user may belong to both a regular group and a managerial group.
    # If that's the case, we want to use their manager settings.
    target_membership = all_intended_members | all_intended_managers
    actual_membership = {member['email']: {'email': member['email'], 'role': member['role']}
                         for member in get_gws_group_members(group_email, gws_members_client)}

    # Unsubscribe extraneous addresses. This needs to be done before adding new
    # emails in order to avoid "member already exists" errors when a subscriber
    # sets their `mailing_list_email` attribute to their username@icecube.wisc.edu
    # address or a non-canonical alias.
    for email in set(actual_membership) - set(target_membership):
        if actual_membership[email]['role'] == 'OWNER':
            # Don't unsubscribe owners. They are managed out-of-band
            continue
        logger.info(f"Removing from {group_email} {email} (dryrun={dryrun})")
        if dryrun:
            continue
        retry_execute(gws_members_client.delete(groupKey=group_email, memberKey=email))
        if send_notifications:
            send_email(email, f"You have been unsubscribed from {group_email}",
                       reflow_text(
                           UNSUBSCRIPTION_MESSAGE.format(
                               group_email=group_email, email=email,
                               role=actual_membership[email]['role'],
                               group_path=kc_root_group['path']),
                           para_sep=PARA_SEP),
                       headline='IceCube Mailing List Management')

    # Build list of owners' canonical emails. Because owners are managed out of band,
    # we can have a situation where an owner who is a member of the Keycloak group is
    # subscribed to the group in Google Workspace as username@icecube.wisc.edu. In
    # this case we need to make sure we don't try to add them using their canonical
    # address (because it will fail).
    actual_owner_canonical_emails = set()
    for owner_email in [e for e, u in actual_membership.items() if u['role'] == 'OWNER']:
        if owner_email.endswith('@icecube.wisc.edu'):
            local_part = owner_email.split('@')[0]
            try:
                user = await cached_user_info(local_part, keycloak_client)
            except UserDoesNotExist:
                # Move on if local_part is not a username or user only exists in GWS
                continue
            actual_owner_canonical_emails.add(user['attributes'].get('canonical_email'))

    for email, body in target_membership.items():
        if email in actual_owner_canonical_emails:
            # Owners are supposed to be managed out-of-band, but this owner is a member
            # of the Keycloak group. We can't rely on normal membership check because
            # the owner may have been configured in Google Workspace using username@i.w.e
            # instead of the canonical address.
            continue
        if email not in actual_membership:
            logger.info(f"Inserting into {group_email} {body} (dryrun={dryrun})")
            if dryrun:
                continue
            retry_execute(gws_members_client.insert(groupKey=group_email, body=body))
            if send_notifications:
                send_email(email, f"You have been subscribed to {group_email}",
                           reflow_text(
                               SUBSCRIPTION_MESSAGE.format(
                                   group_email=group_email, email=email, role=body['role'],
                                   delivery=body['delivery_settings'],
                                   qualifying_groups=', '.join(member_kc_groups[email]),
                                   none_explanation=(PARA_SEP + NONE_EXPLANATION
                                                     if body['delivery_settings'] == 'NONE'
                                                     else '')),
                               para_sep=PARA_SEP),
                           headline='IceCube Mailing List Management')
        # If email already subscribed, check if we need to update the role
        elif body['role'] != actual_membership[email]['role']:
            logger.info(f"Patching in {group_email} role of {email} to {body['role']} (dryrun={dryrun})")
            if dryrun:
                continue
            retry_execute(gws_members_client.patch(groupKey=group_email, memberKey=email,
                                                   body={'email': email, 'role': body['role']}))
            if send_notifications:
                send_email(email, f"Your member role in {group_email} has changed",
                           reflow_text(
                               ROLE_CHANGE_MESSAGE.format(
                                   group_email=group_email, email=email,
                                   old_role=actual_membership[email]['role'],
                                   new_role=body['role'], group_path=kc_root_group['path']),
                               para_sep=PARA_SEP),
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

    See file docstring for detailed documentation.

    Args:
        gws_members_client (googleapiclient.discovery.Resource): Directory API's Members resource
        gws_groups_client (googleapiclient.discovery.Resource): Directory API's Groups resource
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        single_group (str): only consider this group instead of all groups
        send_notifications (bool): whether to send email notifications
        dryrun (bool): Perform a mock run with no changes made
    """
    res = retry_execute(gws_groups_client.list(customer='my_customer'))
    gws_group_emails = [g['email'] for g in res.get('groups', [])]

    kc_ml_group_root = await group_info('/mail', rest_client=keycloak_client)
    if single_group:
        logger.warning(f"Only group {single_group} will be considered.")
        kc_ml_groups = [sg for sg in kc_ml_group_root['subGroups'] if sg['name'] == single_group]
    else:
        kc_ml_groups = kc_ml_group_root['subGroups']
    for kc_ml_group in kc_ml_groups:
        if not (group_email := kc_ml_group['attributes'].get('email')):
            logger.warning(f"Attribute 'email' of {kc_ml_group['path']} is missing or empty'. Skipping.")
            continue
        if group_email not in gws_group_emails:
            logger.error(f"Group '{group_email}' doesn't exist in Google Workspace. Skipping.")
            continue

        # Sanity check. Subgroups of mail groups shouldn't have attribute 'email',
        # and if they do, it definitely can't be different from the root mail group.
        for subgroup in group_tree_to_list(kc_ml_group)[1:]:
            if sg_email := subgroup.get('attributes', {}).get('email'):
                if sg_email == group_email:
                    logger.warning(f"Group {subgroup['path']} shouldn't define attribute 'email'.")
                else:
                    logger.error(f"Group {subgroup['path']} defines email={sg_email},"
                                 f" which is different from {kc_ml_group['path']}'s email={group_email}."
                                 f"This is not allowed. Skipping {kc_ml_group['path']}")
                    continue

        await sync_kc_group_tree_to_gws(kc_ml_group, group_email, keycloak_client, gws_members_client,
                                        send_notifications, dryrun)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Synchronize memberships of Google Workspace groups to their '
                    'corresponding Keycloak mailing list groups. Optionally, '
                    'notify users of changes. See file docstring for detailed '
                    'documentation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='See module docstring for details, including SMTP server configuration.')
    parser.add_argument('--sa-credentials', metavar='PATH', required=True,
                        help='JSON file with service account credentials')
    parser.add_argument('--sa-subject', metavar='EMAIL', required=True,
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
        args['sa_credentials'], subject=args['sa_subject'],
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
