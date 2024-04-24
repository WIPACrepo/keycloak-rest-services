"""
Look up group member emails.

Example::

    ./setupenv.sh
    . env/bin/activate
    python scripts/get_group_member_emails.py /mail/wg-leaders/_admin
"""

import asyncio
import logging

from asyncache import cached
from cachetools import TTLCache

from krs.token import get_rest_client
from krs.users import user_info
from krs.groups import get_group_membership


@cached(TTLCache(1024, 60))
async def get_name(username, client=None):
    ret = await user_info(username, rest_client=client)
    return ret['firstName']+' '+ret['lastName']


@cached(TTLCache(1024, 60))
async def get_email(username, client=None):
    ret = await user_info(username, rest_client=client)
    return ret.get('attributes', {}).get('canonical_email', ret.get('email', None))


async def run(group, client=None):
    members = await get_group_membership(group, rest_client=client)
    emails = [await get_email(user, client=client) for user in members]
    print(', '.join(e for e in emails if e))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--log-level', default='warning', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    parser.add_argument('group', help='group path')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(run(args['group'], client=keycloak_client))


if __name__ == '__main__':
    main()
