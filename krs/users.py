"""
User actions against Keycloak.
"""
import requests

from .util import config, ConfigRequired

def list_users(token=None):
    """
    List users in Keycloak.

    Returns:
        dict: username: user info
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
        'max_users': 10000,
    })
    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users?max={cfg["max_users"]}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = {}
    for u in r.json():
        ret[u['username']] = u
    return ret

def user_info(username, token=None):
    """
    Get user information.

    Args:
        username (str): username of user

    Returns:
        dict: user info
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users?username={username}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = r.json()

    if not ret:
        raise Exception(f'user "{username}" does not exist')
    return ret[0]

def create_user(username, first_name, last_name, email, attribs=None, token=None):
    """
    Create a user in Keycloak.

    Args:
        username (str): username of user to create
        first_name (str): first name
        last_name (str): last name
        email (str): email address
        attribs (dict): user attributes
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    try:
        user_info(username, token=token)
    except Exception:
        print(f'creating user "{username}"')
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users'
        user = {
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'username': username,
            'enabled': True,
            'attributes': {item.split('=',1)[0]:item.split('=',1)[-1] for item in attribs},
        }
        print(user)
        r = requests.post(url, json=user, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'user "{username}" created')
    else:
        print(f'user "{username}" already exists')

def set_user_password(username, password=None, token=None):
    """
    Set a user's password in Keycloak.

    Args:
        username (str): username of user
        password (str): new password
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    if password is None:
        # get password from cmdline
        import getpass
        password = getpass.getpass()

    try:
        ret = user_info(username, token=token)
    except Exception:
        print(f'user "{username}" does not exist')
    else:
        user_id = ret['id']
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users/{user_id}/reset-password'
        args = {
            'value': password,
        }
        r = requests.put(url, json=args, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'user "{username}" password set')

def delete_user(username, token=None):
    """
    Delete a user in Keycloak.

    Args:
        username (str): username of user to delete
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    try:
        ret = user_info(username, token=token)
    except Exception:
        print(f'user "{username}" does not exist')
    else:
        user_id = ret['id']
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users/{user_id}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'user "{username}" deleted')

def main():
    import argparse
    from pprint import pprint
    from .token import get_token

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
    parser_set_password = subparsers.add_parser('set_password', help='set a user\'s password')
    parser_set_password.add_argument('username', help='user name')
    parser_set_password.add_argument('--password', default=None, help='password')
    parser_set_password.set_defaults(func=set_user_password)
    parser_delete = subparsers.add_parser('delete', help='delete a user')
    parser_delete.add_argument('username', help='user name')
    parser_delete.set_defaults(func=delete_user)
    args = parser.parse_args()

    token = get_token()

    args = vars(args)
    func = args.pop('func')
    ret = func(token=token, **args)
    if ret is not None:
        pprint(ret)

if __name__ == '__main__':
    main()