"""
Update user attributes that track users' institutions:
* institutions_last_seen: coma-separated list of the user's institutions (group
                          paths) as of the last time this action ran. Special
                          value "none" indicates the user is institutionless.
* institutions_last_changed: time in ISO 8601 format when institutions_last_seen
                             of the user was last updated.

Note that the reason institutions_last_seen is a comma-separated list is that
currently our KeyCloak instance can't store lists as user attribute values.
The special value "none" is necessary because Keycloak 22 (and later?) deletes
attributes that are empty or are set to the empty string, which can be confusing.

When a user's institutions change, they can optionally be alerted to
this fact via email. SMTP server is controlled by the EMAIL_SMTP_SERVER
environmental variable and defaults to localhost. See krs/email.py for
more email options.

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes

Example::
    python -m actions.track_user_institutions --dryrun
"""
import asyncio
import logging
from datetime import datetime
from collections import defaultdict
from requests.exceptions import HTTPError

from krs.token import get_rest_client
from krs.groups import get_group_membership
from krs.institutions import list_insts
from krs.users import list_users, modify_user
from krs.email import send_email

logger = logging.getLogger('track_user_institutions')

INSTITUTIONS_CHANGED_MESSAGE = """
According to our identity management system, your institutions have changed
from {old} to {new}.

Your access to institution-dependent resources, such as some mailing lists,
will change accordingly.

If you believe this is a mistake, please join the appropriate institution(s)
on https://user-management.icecube.aq, or email help@icecube.wisc.edu.

This message has been generated by the track_user_institutions robot.
"""


async def update_institution_tracking(keycloak_client=None, notify=True, dryrun=False):
    """Update institutions_last_seen and institutions_last_changed user attributes.

    Args:
        keycloak_client (OpenIDRestClient): REST client to the KeyCloak server
        notify (bool): send out notification emails
        dryrun (bool): perform a trial run with no changes made
    """

    user_insts = defaultdict(list)
    insts = await list_insts(rest_client=keycloak_client)
    for inst_path in insts.keys():
        inst_usernames = await get_group_membership(inst_path, rest_client=keycloak_client)
        for inst_username in inst_usernames:
            user_insts[inst_username].append(inst_path)

    all_users = await list_users(rest_client=keycloak_client)
    for username, userinfo in all_users.items():
        insts_actual = user_insts[username]
        # There's currently an issue with our keycloak that prevents using lists
        # as user attribute values. To work-around, institutions_last_seen is
        # stored as comma-separated string.
        insts_last_seen_str = userinfo["attributes"].get("institutions_last_seen", "none")
        if insts_last_seen_str == "none":
            insts_last_seen = []
        else:
            insts_last_seen = [i.strip() for i in insts_last_seen_str.split(',') if i.strip()]
        if set(insts_actual) != set(insts_last_seen):
            logger.info(f"{username}'s institutions have changed from "
                        f"{insts_last_seen} to {insts_actual}")
            # Keycloak 22 deletes attributes set to empty string, so use "none"
            # instead, to make this code future-proof.
            attribs = {"institutions_last_seen": (','.join(insts_actual) or "none"),
                       "institutions_last_changed": datetime.now().isoformat()}
            if dryrun:
                continue
            try:
                await modify_user(username, attribs=attribs, rest_client=keycloak_client)
            except HTTPError as exc:
                if exc.response.status_code == 400:
                    logger.info(f"Got HTTP 400 (bad request): {repr(exc)}")
                    logger.info("Field probably failed validation. Invalid 'email' is often the cause.")
                    continue
                else:
                    raise
            if notify:
                logger.info(f"Notifying {username} of institution change")
                send_email(userinfo.get('email', f"{username}@icecube.wisc.edu"),
                           "Your WIPAC institution registration has changed",
                           INSTITUTIONS_CHANGED_MESSAGE.format(
                               old=', '.join(insts_last_seen) or "none",
                               new=', '.join(insts_actual) or "none"))


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Update institutions_last_seen and institutions_last_changed user '
                    'attributes. See file docstring for details.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--notify', action='store_true', help='send notification emails (see module docstring)')
    parser.add_argument('--dryrun', action='store_true', help='dry run (implies no notifications)')
    parser.add_argument('--log-level', default='info',
                        choices=('debug', 'info', 'warning', 'error'), help='logging level')

    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()
    asyncio.run(update_institution_tracking(
        keycloak_client=keycloak_client,
        notify=args['notify'],
        dryrun=args['dryrun']))


if __name__ == '__main__':
    main()
