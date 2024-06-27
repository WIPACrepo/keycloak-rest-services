"""
Look up group member emails.

Examples::

    ./setupenv.sh
    . env/bin/activate
    python scripts/get_group_member_emails.py /mail/wg-leaders/_admin
    python scripts/get_group_member_emails.py /institutions/IceCube/*/_admin
    python scripts/get_group_member_emails.py /posix/ARA-filt /posix/ARA-moni
"""

import asyncio
import fnmatch
import logging

from asyncache import cached
from cachetools import TTLCache

from krs.token import get_rest_client
from krs.users import user_info
from krs.groups import list_groups, get_group_membership_by_id


@cached(TTLCache(1024, 60))
async def get_name(username, client=None):
    ret = await user_info(username, rest_client=client)
    return ret['firstName']+' '+ret['lastName']


@cached(TTLCache(1024, 60))
async def get_email(username, client=None):
    ret = await user_info(username, rest_client=client)
    return ret.get('attributes', {}).get('canonical_email', ret.get('email', None))


async def run(groups, client=None):
    emails = set()
    krs_groups = await list_groups(rest_client=client)
    for pattern in groups:
        matches = fnmatch.filter(krs_groups.keys(), pattern)
        for group in sorted(matches):
            print('processing',group)
            group_data = krs_groups[group]
            members = await get_group_membership_by_id(group_data['id'], rest_client=client)
            emails.update([await get_email(user, client=client) for user in members])

    print(', '.join(e for e in emails if e))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', default='warning', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('groups', nargs='+', help='group path(s) - can use glob and list multiple args')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(run(args['groups'], client=keycloak_client))


if __name__ == '__main__':
    main()
