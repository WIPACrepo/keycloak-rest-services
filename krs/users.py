"""
User actions against Keycloak.

This code uses custom keycloak attributes that are documented here:
https://bookstack.icecube.wisc.edu/ops/books/services/page/custom-keycloak-attributes
"""
import asyncio
import logging
from random import randint
# noinspection PyPackageRequirements
from unidecode import unidecode

# noinspection PyPackageRequirements
import requests.exceptions

from .token import get_rest_client
from .util import fix_singleton_attributes

logger = logging.getLogger('krs.users')


class UserDoesNotExist(Exception):
    pass


async def list_users(search=None, attr_query=None, rest_client=None):
    """
    List users in Keycloak.

    Search and query format and semantics here:
    https://www.keycloak.org/docs-api/24.0.1/rest-api/index.html

    The `search` parameter filters by a string contained in username, first or
    last name, or email. Default search behavior is prefix-based (e.g., foo
    or foo*). Use *foo* for infix search and "foo" for exact search. As of
    Keycloak 24, suffix searching is not possible.

    The `query` parameter filters by custom attributes. It should be of the
    form {'attr_name': 'attr_value', ...}.

    Args:
        search (str|None): username/name/email search (see above)
        attr_query (dict|None): attribute search (see above)
        rest_client (RestClient): Keycloak REST client
    Returns:
        dict: username: user info
    """
    if search and attr_query:
        # As of KeyCloak 24, the q parameter is ignored if search is specified
        raise ValueError("Parameters search and query are mutually exclusive")

    # Validate and if necessary/possible make the queries suitable for embedding in URL
    if attr_query:
        for key, value in attr_query.copy().items():
            if set('&"\'') & (set(str(value)) | set(str(key))):
                raise NotImplementedError(f"Not yet capable of encoding attribute query {attr_query}")
            if ' ' in str(value):
                attr_query[key] = f'"{value}"'
            if ' ' in str(key) or ':' in str(key):
                new_key = f'"{key}"'
                if new_key in attr_query:
                    raise NotImplementedError(f"Not yet capable of encoding attribute {attr_query}")
                attr_query[new_key] = attr_query[key]
                attr_query.pop(key)

    inc = 50
    ret = {}
    num_users = await rest_client.request('GET', '/users/count')
    for start in range(0, num_users, inc):
        url = f'/users?&max={min(inc, num_users - start)}&first={start}'
        if search:
            url += f'&search={search}'
        if attr_query:
            # query format here: https://www.keycloak.org/docs-api/24.0.1/rest-api/index.html
            url += "&q=" + " ".join(f"{key}:{val}" for key, val in attr_query.items())
        data = await rest_client.request('GET', url)
        for u in data:
            fix_singleton_attributes(u)
            ret[u['username']] = u
    return ret


async def user_info(username, rest_client=None):
    """
    Get user information.

    Args:
        username (str): username of user
        rest_client (RestClient): Keycloak REST client

    Returns:
        dict: user info
    """
    url = f'/users?exact=true&username={username}'
    ret = await rest_client.request('GET', url)

    if not ret:
        raise UserDoesNotExist(f'user "{username}" does not exist')
    fix_singleton_attributes(ret[0])
    return ret[0]


async def __address_in_use(address, rest_client):
    if await list_users(attr_query={'canonical_email': address}, rest_client=rest_client):
        return True
    local_part = address.split('@')
    try:
        await user_info(local_part, rest_client=rest_client)
    except UserDoesNotExist:
        return False
    else:
        return True


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
    except UserDoesNotExist:
        pass
    else:
        logger.info(f'user "{username}" already exists')
        return

    if 'canonical_email' in attribs:
        raise NotImplementedError("Support for custom canonical addresses not implemented")
    # Generate a canonical address that is not being used
    name_part = unidecode(first_name + '.' + last_name).lower().replace(' ', '.')
    canonical_email = f"{name_part}@icecube.wisc.edu"
    # If the standard canonical address is in use, generate a "nice" random salt.
    while await __address_in_use(canonical_email, rest_client):
        # The range was chosen to avoid numbers problematic in various cultures, small numbers
        # (e.g. john.doe2@ is just sad), and numbers that look like birth years (e.g. foo.bar91)
        salt = str(randint(100, 600))
        canonical_email = f'{name_part}{salt}@icecube.wisc.edu'
    attribs['canonical_email'] = canonical_email

    logger.info(f'creating user "{username}"')
    user = {
        'email': email,
        'firstName': first_name,
        'lastName': last_name,
        'username': username,
        'enabled': True,
        'attributes': attribs,
    }
    try:
        await rest_client.request('POST', '/users', user)
    except requests.exceptions.HTTPError as e:
        logger.error('Keycloak returned HTTP error %r: %r', e.response.status_code, e.response.text)
        raise
    else:
        logger.info(f'user "{username}" created')


async def modify_user(username, first_name=None, last_name=None, email=None, attribs=None,
                      actions=None, actions_reset=False, rest_client=None):
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
        rest_client (RestClient): Keycloak REST client
    """
    if password is None:
        # get password from cmdline
        import getpass
        password = getpass.getpass()

    if not isinstance(password, str):
        raise Exception('password must be a string')

    try:
        ret = await user_info(username, rest_client=rest_client)
    except UserDoesNotExist:
        logger.info(f'user "{username}" does not exist')
    else:
        url = f'/users/{ret["id"]}/reset-password'
        args = {
            'value': password,
            'temporary': bool(temporary),
        }
        await rest_client.request('PUT', url, args)
        logger.info(f'user "{username}" password set')


async def delete_user(username, rest_client=None):
    """
    Delete a user in Keycloak.

    Args:
        username (str): username of user to delete
        rest_client (RestClient): Keycloak REST client
    """
    try:
        ret = await user_info(username, rest_client=rest_client)
    except UserDoesNotExist:
        logger.info(f'user "{username}" does not exist')
    else:
        url = f'/users/{ret["id"]}'
        await rest_client.request('DELETE', url)
        logger.info(f'user "{username}" deleted')


def main():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='Keycloak user management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list users')
    parser_list.add_argument('--search', default=None, help='search string')
    parser_list.add_argument('--attr-query', nargs='+', default=None, metavar='NAME VALUE',
                             help='query by conjunction of custom attributes')
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
    parser_modify.add_argument('--actions', action='append', help='required actions',
                               choices=['CONFIGURE_TOTP', 'UPDATE_PASSWORD', 'UPDATE_PROFILE', 'VERIFY_EMAIL'])
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
    if 'attr_query' in args:
        query_pairs = args['attr_query']
        if len(query_pairs) % 2:
            parser.error('The number of arguments to --attr-query must be even')
        args['attr_query'] = dict(zip(query_pairs[:-1:2], query_pairs[1::2]))
    if 'attribs' in args:
        args['attribs'] = {item.split('=', 1)[0]: item.split('=', 1)[-1] for item in args['attribs']}
    ret = asyncio.run(func(rest_client=rest_client, **args))
    if ret is not None:
        pprint(ret)


if __name__ == '__main__':
    main()
