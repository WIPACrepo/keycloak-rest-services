"""
Look up all users and write them to a csv file.

Examples::

    ./setupenv.sh
    . env/bin/activate
    python scripts/get_users_csv.py users.csv
"""

import asyncio
import csv
import logging

from asyncache import cached
from cachetools import TTLCache

from krs.token import get_rest_client
from krs.users import list_users, user_info


@cached(TTLCache(1024, 60))
async def get_name(username, client=None):
    ret = await user_info(username, rest_client=client)
    return ret['firstName']+' '+ret['lastName']


async def run(client, filename):
    krs_users = await list_users(rest_client=client)
    ret = {}
    data = {}
    fieldnames = set()
    for user in krs_users:
        data = krs_users[user]
        data.update(data.pop('attributes', {}))
        ret[user] = data
        fieldnames.update(data.keys())

    if ret:
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ret.values())
    else:
        logging.warning('no users found!')


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='csv filename to write to')
    parser.add_argument('--log-level', default='warning', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(run(client=keycloak_client, filename=args['filename']))


if __name__ == '__main__':
    main()
