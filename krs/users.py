"""
User actions against Keycloak.
"""
import asyncio

from .token import get_rest_client

async def list_users(max_users=10000, rest_client=None):
    """
    List users in Keycloak.

    Returns:
        dict: username: user info
    """
    url = f'/users?max={max_users}'
    data = await rest_client.request('GET', url)
    ret = {}
    for u in data:
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
    url = f'/users?username={username}'
    ret = await rest_client.request('GET', url)

    if not ret:
        raise Exception(f'user "{username}" does not exist')
    if 'attributes' in ret[0]:
        for k in ret[0]['attributes']:
            if len(ret[0]['attributes'][k]) == 1:
                ret[0]['attributes'][k] = ret[0]['attributes'][k][0]
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
        print(f'creating user "{username}"')
        print(username)
        user = {
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'username': username,
            'enabled': True,
            'attributes': attribs,
        }

        await rest_client.request('POST', '/users', user)
        print(f'user "{username}" created')
    else:
        print(f'user "{username}" already exists')

async def modify_user(username, attribs=None, rest_client=None):
    """
    Modify a user in Keycloak.

    Args:
        username (str): username of user to modify
        attribs (dict): user attributes
        rest_client: keycloak rest client
    """
    if not attribs:
        attribs = {}

    # get current user info
    try:
        ret = await user_info(username, rest_client=rest_client)
    except Exception:
        print(f'user "{username}" does not exist')

    url = f'/users/{ret["id"]}'
    ret = await rest_client.request('GET', url)

    # update info
    if 'attributes' in ret:
        ret['attributes'].update(attribs)
    else:
        ret['attributes'] = attribs
    await rest_client.request('PUT', url, ret)

async def set_user_password(username, password=None, rest_client=None):
    """
    Set a user's password in Keycloak.

    Args:
        username (str): username of user
        password (str): new password
    """
    if password is None:
        # get password from cmdline
        import getpass
        password = getpass.getpass()

    try:
        ret = await user_info(username, rest_client=rest_client)
    except Exception:
        print(f'user "{username}" does not exist')
    else:
        url = f'/users/{ret["id"]}/reset-password'
        args = {
            'value': password,
        }
        ret = await rest_client.request('PUT', url, args)
        print(f'user "{username}" password set')

async def delete_user(username, rest_client=None):
    """
    Delete a user in Keycloak.

    Args:
        username (str): username of user to delete
    """
    try:
        ret = await user_info(username, rest_client=rest_client)
    except Exception:
        print(f'user "{username}" does not exist')
    else:
        url = f'/users/{ret["id"]}'
        ret = await rest_client.request('DELETE', url)
        print(f'user "{username}" deleted')

def main():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='Keycloak user management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list users')
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
    parser_modify.add_argument('attribs', nargs=argparse.REMAINDER)
    parser_modify.set_defaults(func=modify_user)
    parser_set_password = subparsers.add_parser('set_password', help='set a user\'s password')
    parser_set_password.add_argument('username', help='user name')
    parser_set_password.add_argument('--password', default=None, help='password')
    parser_set_password.set_defaults(func=set_user_password)
    parser_delete = subparsers.add_parser('delete', help='delete a user')
    parser_delete.add_argument('username', help='user name')
    parser_delete.set_defaults(func=delete_user)
    args = vars(parser.parse_args())

    rest_client = get_rest_client()
    func = args.pop('func')
    if 'attribs' in args:
        args['attribs'] = {item.split('=', 1)[0]: item.split('=', 1)[-1] for item in args['attribs']}
    ret = asyncio.run(func(rest_client=rest_client, **args))
    if ret is not None:
        pprint(ret)

if __name__ == '__main__':
    main()
