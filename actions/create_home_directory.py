"""
Creates a home directory for anyone with the attribute.

Creates directories of the style /home/<username> relative
to a root directory.

Example::

    python actions/create_home_directory.py --root-dir /foo/bar

This will create user home dirs with directories like `/foo/bar/home/user1`.

"""
import os
import logging
import asyncio
import getpass
import pathlib

from krs.users import list_users
from krs.token import get_rest_client


logger = logging.getLogger('create_home_directory')

async def process(root_dir, keycloak_client=None):
    ret = await list_users(rest_client=keycloak_client)
    for username in ret:
        user = ret[username]
        if ('attributes' in user and 'homeDirectory' in user['attributes']
                and 'uidNumber' in user['attributes']
                and 'gidNumber' in user['attributes']):
            homedir = user['attributes']['homeDirectory']
            if homedir.startswith('/'):
                homedir = homedir[1:]
            path = root_dir / homedir
            if not path.exists():
                logger.info(f'creating home directory at {path}')
                path.mkdir(mode=0o755, parents=True, exist_ok=True)
                if getpass.getuser() == 'root':
                    os.chown(path, int(user['attributes']['uidNumber']), int(user['attributes']['gidNumber']))
                else:
                    logger.debug('skipping chown because we are not root')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Create home directories')
    parser.add_argument('--root-dir', default='/', type=pathlib.Path, help='root directory to create home user directories in (default=/)')
    parser.add_argument('--log_level', default='info', choices=('debug', 'info', 'warning', 'error'), help='logging level')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))

    keycloak_client = get_rest_client()

    asyncio.run(process(args['root_dir'], keycloak_client=keycloak_client))


if __name__ == '__main__':
    main()
