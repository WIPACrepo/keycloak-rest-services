"""
User actions against Keycloak.
"""
import asyncio
import logging

from .token import get_rest_client

logger = logging.getLogger('krs.users')


def _fix_attributes(user):
    """
    "Fix" user attributes that are only a single value.

    Translates them from a list to the single value.  Operation
    is done in-place.

    Args:
        user (dict): user object
    """
    if 'attributes' in user:
        for k in user['attributes']:
            if len(user['attributes'][k]) == 1:
                user['attributes'][k] = user['attributes'][k][0]


class UserDoesNotExist(Exception):
    pass


async def list_users(search=None, rest_client=None):
    """
    List users in Keycloak.

    Returns:
        dict: username: user info
    """
    start = 0
    inc = 50
    ret = {}
    data = [0]*inc

    while len(data) == inc:
        url = f'/users?&max={inc}&first={start}'
        if search:
            url += f'&search={search}'
        data = await rest_client.request('GET', url)
        start += inc
        for u in data:
            _fix_attributes(u)
            ret[u['username']] = u
    return ret


async def user_info(username, rest_client=None):
    """
    Get user information.

    Args:
        username (str): username of user

    Returns:
        dict: user info
    """
    url = f'/users?exact=true&username={username}'
    ret = await rest_client.request('GET', url)

    if not ret:
        raise UserDoesNotExist(f'user "{username}" does not exist')
    _fix_attributes(ret[0])
    return ret[0]


async def create_user(username, first_name, last_name, email, attribs=None, rest_client=None):
    """
    Create a user in Keycloak.

    Args:
        username (str): username of user to create
        first_name (str): first name
        last_name (str): last name
        email (str): email address
        attribs (dict): user attributes
        rest_client: keycloak rest client
    """
    if not attribs:
        attribs = {}

    try:
        await user_info(username, rest_client=rest_client)
    except Exception:
        logger.info(f'creating user "{username}"')
        logger.info(username)
        user = {
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'username': username,
            'enabled': True,
            'attributes': attribs,
        }

        await rest_client.request('POST', '/users', user)
        logger.info(f'user "{username}" created')
    else:
        logger.info(f'user "{username}" already exists')


async def modify_user(username, first_name=None, last_name=None, email=None, attribs=None, actions=None, actions_reset=False, rest_client=None):
    """
    Modify a user in Keycloak.

    Args:
        username (str): username of user to modify
        first_name (str): first name
        last_name (str): last name
        email (str): email address
        attribs (dict): user attributes
        actions (list): required actions
        actions_reset (bool): reset required actions
        rest_client: keycloak rest client
    """
    # do some assertions to save on strange keycloak errors
    if first_name and not isinstance(first_name, str):
        raise RuntimeError('first_name must be a string')
    if last_name and not isinstance(last_name, str):
        raise RuntimeError('last_name must be a string')
    if email and not isinstance(email, str):
        raise RuntimeError('email must be a string')
    if not attribs:
        attribs = {}
    if not actions:
        actions = []
    if not all(a in ['CONFIGURE_TOTP', 'UPDATE_PASSWORD', 'UPDATE_PROFILE', 'VERIFY_EMAIL'] for a in actions):
        raise RuntimeError('actions are invalid')

    # get current user info
    try:
        ret = await user_info(username, rest_client=rest_client)
    except Exception:
        logger.info(f'user "{username}" does not exist')
        raise

    url = f'/users/{ret["id"]}'
    ret = await rest_client.request('GET', url)

    # update info
    if first_name:
        ret['firstName'] = first_name
    if last_name:
        ret['lastName'] = last_name
    if email:
        ret['email'] = email
    if 'attributes' not in ret:
        ret['attributes'] = {}
    for k in attribs:
        if attribs[k] is None:
            ret['attributes'].pop(k, None)
        elif isinstance(attribs[k], list):
            ret['attributes'][k] = attribs[k]
        else:
            ret['attributes'][k] = [attribs[k]]
    if not actions_reset:
        actions = list(set(actions) | set(ret['requiredActions']))
    ret['requiredActions'] = actions
    await rest_client.request('PUT', url, ret)


async def set_user_password(username, password=None, temporary=False, rest_client=None):
    """
    Set a user's password in Keycloak.

    Args:
        username (str): username of user
        password (str): new password
        temporary (bool): is this a temporary password that must be changed?
    """
    if password is None:
        # get password from cmdline
        import getpass
        password = getpass.getpass()

    if not isinstance(password, str):
        raise Exception('password must be a string')

    try:
        ret = await user_info(username, rest_client=rest_client)
    except Exception:
        logger.info(f'user "{username}" does not exist')
    else:
        url = f'/users/{ret["id"]}/reset-password'
        args = {
            'value': password,
            'temporary': bool(temporary),
        }
        ret = await rest_client.request('PUT', url, args)
        logger.info(f'user "{username}" password set')


async def delete_user(username, rest_client=None):
    """
    Delete a user in Keycloak.

    Args:
        username (str): username of user to delete
    """
    try:
        ret = await user_info(username, rest_client=rest_client)
    except Exception:
        logger.info(f'user "{username}" does not exist')
    else:
        url = f'/users/{ret["id"]}'
        ret = await rest_client.request('DELETE', url)
        logger.info(f'user "{username}" deleted')


def main():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='Keycloak user management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list users')
    parser_list.add_argument('--search', default=None, help='search string')
    parser_list.set_defaults(func=list_users)
    parser_info = subparsers.add_parser('info', help='user info')
    parser_info.add_argument('username', help='user name')
    parser_info.set_defaults(func=user_info)
    parser_create = subparsers.add_parser('create', help='create a new user')
    parser_create.add_argument('username', help='user name')
    parser_create.add_argument('first_name', help='first name')
    parser_create.add_argument('last_name', help='last name')
    parser_create.add_argument('email', help='email address')
    parser_create.add_argument('attribs', nargs=argparse.REMAINDER)
    parser_create.set_defaults(func=create_user)
    parser_modify = subparsers.add_parser('modify', help='modify an existing user')
    parser_modify.add_argument('username', help='user name')
    parser_modify.add_argument('--first_name', help='first name')
    parser_modify.add_argument('--last_name', help='last name')
    parser_modify.add_argument('--email', help='email address')
    parser_modify.add_argument('--actions', action='append', help='required actions', choices=['CONFIGURE_TOTP', 'UPDATE_PASSWORD', 'UPDATE_PROFILE', 'VERIFY_EMAIL'])
    parser_modify.add_argument('--actions-reset', action='store_true', help='reset required actions')
    parser_modify.add_argument('attribs', nargs=argparse.REMAINDER)
    parser_modify.set_defaults(func=modify_user)
    parser_set_password = subparsers.add_parser('set_password', help='set a user\'s password')
    parser_set_password.add_argument('username', help='user name')
    parser_set_password.add_argument('--password', default=None, help='password')
    parser_set_password.add_argument('--temporary', default=False, action='store_true', help='is password temporary?')
    parser_set_password.set_defaults(func=set_user_password)
    parser_delete = subparsers.add_parser('delete', help='delete a user')
    parser_delete.add_argument('username', help='user name')
    parser_delete.set_defaults(func=delete_user)
    args = vars(parser.parse_args())

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rest_client = get_rest_client()
    func = args.pop('func')
    if 'attribs' in args:
        args['attribs'] = {item.split('=', 1)[0]: item.split('=', 1)[-1] for item in args['attribs']}
    ret = asyncio.run(func(rest_client=rest_client, **args))
    if ret is not None:
        pprint(ret)


if __name__ == '__main__':
    main()
