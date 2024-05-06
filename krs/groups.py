"""
Group actions against Keycloak.
"""
import asyncio
import logging
from requests.exceptions import HTTPError

from .token import get_rest_client
from .users import user_info
from .util import fix_singleton_attributes

logger = logging.getLogger('krs.groups')

# Keycloak 23 introduced a breaking change where calls to various group-related
# REST endpoints no longer populate the subGroups attribute of the returned group
# objects (https://github.com/keycloak/keycloak/issues/27694). In some cases there
# is no work-around, and GET to the /admin/realms/{realm}/groups/{group-id}/children
# endpoint is needed. That endpoint doesn't exist in versions prior to 23. This global
# variable will be set to True/False once we determine whether the endpoint exists.
KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT = None


def _recursive_fix_group_attributes(group):
    """
    Recursively "fix" group tree attributes that are singleton lists.

    Translates them from a list to the single value.  Operation
    is done in-place.

    Args:
        group (dict): group object
    """
    fix_singleton_attributes(group)
    for subgroup in group['subGroups']:
        _recursive_fix_group_attributes(subgroup)


class GroupDoesNotExist(Exception):
    pass


async def get_group_hierarchy(*, rest_client):
    """
    Return the entire group hierarchy tree.

    Return value is a list of top-level GroupRepresentation dicts with
    subGroups recursively populated.

    This function is intended to hide quirks of Keycloak REST API's /groups
    endpoint, whose behavior can be counter-intuitive and has been known
    to change without notice.

    Keycloak REST API GroupRepresentation reference:
    https://www.keycloak.org/docs-api/24.0.3/rest-api/index.html#GroupRepresentation

    Args:
        rest_client (RestClient): Keycloak rest client

    Returns:
        list: list of top-level groups as GroupRepresentations
    """
    # As of Keycloak 23.0.3, subGroups are not populated regardless of
    # the value of `populateHierarchy` of unless `q` or `search` parameters
    # are used. Using `search=` is much faster than using `q=`.
    url = "/groups?briefRepresentation=false&populateHierarchy=true&search="
    ret = await rest_client.request('GET', url)
    for grp in ret:
        _recursive_fix_group_attributes(grp)
    return ret


async def list_groups(max_groups=10000, rest_client=None):
    """
    List all groups in Keycloak.

    Returns a dict of simplified group representations keyed on group path.

    Returns:
        dict: groupname: group details
    """
    # Starting with KeyCloak 23, GET /admin/realms/{realm}/groups doesn't populate
    # subgroups unless "search" parameter is used. It is not clear whether it's
    # a bug or a feature https://github.com/keycloak/keycloak/issues/27694
    url = f'/groups?max={max_groups}&briefRepresentation=false&search='
    group_hierarchy = await rest_client.request('GET', url)
    ret = {}

    def add_groups(groups):
        for g in groups:
            fix_singleton_attributes(g)
            ret[g['path']] = {
                'id': g['id'],
                'name': g['name'],
                'path': g['path'],
                'children': [gg['name'] for gg in g['subGroups']],
                'attributes': g.get('attributes', {}),
            }
            if g['subGroups']:
                add_groups(g['subGroups'])
    add_groups(group_hierarchy)
    return ret


async def group_info(group_path, rest_client=None):
    """
    Get group information.

    Args:
        group_path (str): group path (/parent/parent/name)

    Returns:
        dict: group info
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path not in groups:
        raise GroupDoesNotExist(f'group "{group_path}" does not exist')

    group_id = groups[group_path]['id']
    return await group_info_by_id(group_id, rest_client=rest_client)


async def _keycloak_doesnt_populate_subgroups(group_id, rest_client):
    """
    Return True if the Keycloak server we are dealing with has the
    /admin/realms/{realm}/groups/{group-id}/children endpoint.

    Args:
        group_id (str): id of an existing group
    """
    global KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT

    # Set KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT if it hasn't been set yet
    if KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT is None:
        # If the probing request we are about to issue fails with a 405 (method
        # not allowed), at log level INFO, rest_client will log an exception with
        # traceback, which would be confusing. As a work-around, temporarily raise
        # the logging level of rest_client if necessary.
        saved_rest_client_log_level = rest_client.logger.getEffectiveLevel()
        if saved_rest_client_log_level == logging.getLevelName('INFO'):
            rest_client.logger.setLevel('WARNING')
        try:
            await rest_client.request("GET", f"/groups/{group_id}/children")
        except HTTPError as exc:
            if exc.response.status_code == 405:  # Method Not Allowed
                KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT = False
            else:
                raise
        else:
            KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT = True
        finally:
            rest_client.logger.setLevel(saved_rest_client_log_level)

    return KEYCLOAK_HAS_GROUP_CHILDREN_ENDPOINT


async def _recursive_populate_subgroups(grp, rest_client=None):
    """
    Recursively populate the subGroups attribute of grp.

    Args:
        grp (dict): KeyCloak REST API GroupRepresentation
    """
    start = 0
    inc = 50
    page = [None] * inc
    while len(page) == inc:
        url = f"/groups/{grp['id']}/children?max={inc}&first={start}"
        start += inc
        page = await rest_client.request("GET", url)
        children = [await _recursive_populate_subgroups(g, rest_client) for g in page]
        grp['subGroups'].extend(children)
    return grp


async def group_info_by_id(group_id, rest_client=None):
    """
    Get group information.

    Args:
        group_id (str): group id

    Returns:
        dict: group info
    """
    url = f'/groups/{group_id}'
    ret = await rest_client.request('GET', url)

    if not ret:
        raise GroupDoesNotExist(f'group "{group_id}" does not exist')

    if await _keycloak_doesnt_populate_subgroups(group_id, rest_client):
        await _recursive_populate_subgroups(ret, rest_client)
    _recursive_fix_group_attributes(ret)
    return ret


async def create_group(group_path, attrs=None, rest_client=None):
    """
    Create a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
        attrs (dict): attributes
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path in groups:
        logger.info(f'group "{group_path}" already exists')
    else:
        if '/' not in group_path:
            raise Exception('"group_path" must start with /')
        parent, groupname = group_path.rsplit('/', 1)
        if parent:
            if parent not in groups:
                raise GroupDoesNotExist(f'parent group {parent} does not exist')
            parent_id = groups[parent]['id']
            url = f'/groups/{parent_id}/children'
        else:
            url = '/groups'

        logger.info(f'creating group "{group_path}"')
        group = {
            'name': groupname,
        }
        if attrs:
            group['attributes'] = {k: [attrs[k]] for k in attrs}
        await rest_client.request('POST', url, group)
        logger.info(f'group "{group_path}" created')


async def modify_group(group_path, attrs={}, new_group_name=None, rest_client=None):
    """
    Modify attributes for a group.

    Patches attributes with existing ones.  Use `None` to remove attr.

    Can also rename the group path.

    Args:
        group_path (str): group path (/parent/parent/name)
        attrs (dict): attributes to modify
        new_group_name (str): new group name
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path in groups:
        url = f'/groups/{groups[group_path]["id"]}'
        ret = await rest_client.request('GET', url)
        for k in attrs:
            if attrs[k] is None:
                ret['attributes'].pop(k, None)
            elif isinstance(attrs[k], list):
                ret['attributes'][k] = attrs[k]
            else:
                ret['attributes'][k] = [attrs[k]]
        if new_group_name:
            ret['name'] = new_group_name
            ret['path'] = ret['path'].rsplit('/', 1)[0] + '/' + new_group_name
        await rest_client.request('PUT', url, ret)
        logger.info(f'group "{group_path}" modified')
    else:
        logger.info(f'group "{group_path}" does not exist')


async def delete_group(group_path, rest_client=None):
    """
    Delete a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path in groups:
        url = f'/groups/{groups[group_path]["id"]}'
        await rest_client.request('DELETE', url)
        logger.info(f'group "{group_path}" deleted')
    else:
        logger.info(f'group "{group_path}" does not exist')


async def get_group_membership(group_path, rest_client=None):
    """
    Get the membership list of a group.

    Args:
        group_path (str): group path (/parent/parent/name)

    Returns:
        list: usernames
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path not in groups:
        raise GroupDoesNotExist(f'group "{group_path}" does not exist')
    group_id = groups[group_path]['id']

    return await get_group_membership_by_id(group_id, rest_client=rest_client)


async def get_group_membership_by_id(group_id, rest_client=None):
    """
    Get the membership list of a group.

    This is a paginated request that is fairly slow when linked with LDAP.

    Args:
        group_id (str): group id

    Returns:
        list: usernames
    """
    start = 0
    inc = 50
    ret = []
    data = [0]*inc

    while len(data) == inc:
        url = f'/groups/{group_id}/members?briefRepresentation=true&max={inc}&first={start}'
        start += inc
        data = await rest_client.request('GET', url)
        for user in data:
            ret.append(user['username'])
    return ret


async def get_user_groups(username, rest_client=None):
    """
    Get the groups a user has membership in.

    Args:
        username (str): username of user

    Returns:
        list: group paths
    """
    info = await user_info(username, rest_client=rest_client)
    return await get_user_groups_by_id(info['id'], rest_client=rest_client)


async def get_user_groups_by_id(user_id, rest_client=None):
    """
    Get the groups a user has membership in.

    Args:
        user_id (str): user id of user

    Returns:
        list: group paths
    """
    url = f'/users/{user_id}/groups'
    data = await rest_client.request('GET', url)

    ret = []
    for g in data:
        ret.append(g['path'])
    return ret


async def add_user_group(group_path, username, rest_client=None):
    """
    Add a user to a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
        username (str): username of user
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path not in groups:
        raise GroupDoesNotExist(f'group "{group_path}" does not exist')

    info = await user_info(username, rest_client=rest_client)
    membership = await get_user_groups_by_id(info['id'], rest_client=rest_client)

    if group_path in membership:
        logger.info(f'user "{username}" already a member of group "{group_path}"')
    else:
        # need to temp-remove child groups
        # https://issues.redhat.com/browse/KEYCLOAK-11298
        for group in membership:
            if group.startswith(group_path):
                url = f'/users/{info["id"]}/groups/{groups[group]["id"]}'
                await rest_client.request('DELETE', url)

        url = f'/users/{info["id"]}/groups/{groups[group_path]["id"]}'
        await rest_client.request('PUT', url)

        for group in membership:
            if group.startswith(group_path):
                url = f'/users/{info["id"]}/groups/{groups[group]["id"]}'
                await rest_client.request('PUT', url)

        logger.info(f'user "{username}" added to group "{group_path}"')


async def remove_user_group(group_path, username, rest_client=None):
    """
    Remove a user from a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
        username (str): username of user
    """
    groups = await list_groups(rest_client=rest_client)
    if group_path not in groups:
        raise GroupDoesNotExist(f'group "{group_path}" does not exist')

    info = await user_info(username, rest_client=rest_client)
    membership = await get_user_groups_by_id(info['id'], rest_client=rest_client)

    if group_path not in membership:
        logger.info(f'user "{username}" not a member of group "{group_path}"')
    else:
        url = f'/users/{info["id"]}/groups/{groups[group_path]["id"]}'
        await rest_client.request('DELETE', url)
        logger.info(f'user "{username}" removed from group "{group_path}"')


def main():
    import argparse
    from pprint import pprint
    from collections import defaultdict

    parser = argparse.ArgumentParser(description='Keycloak group management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list groups')
    parser_list.set_defaults(func=list_groups)
    parser_info = subparsers.add_parser('info', help='group info')
    parser_info.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_info.set_defaults(func=group_info)
    parser_create = subparsers.add_parser('create', help='create a new group')
    parser_create.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_create.set_defaults(func=create_group)
    parser_delete = subparsers.add_parser('delete', help='delete a group')
    parser_delete.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_delete.set_defaults(func=delete_group)
    parser_get_members = subparsers.add_parser('members', help='get group membership')
    parser_get_members.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_get_members.set_defaults(func=get_group_membership)
    parser_get_user_groups = subparsers.add_parser('get_user_groups', help="get a user's group memberships")
    parser_get_user_groups.add_argument('username', help='username of user')
    parser_get_user_groups.set_defaults(func=get_user_groups)
    parser_add_user_group = subparsers.add_parser('add_user_group', help='add a user to a group')
    parser_add_user_group.add_argument('username', help='username of user')
    parser_add_user_group.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_add_user_group.set_defaults(func=add_user_group)
    parser_remove_user_group = subparsers.add_parser('remove_user_group', help='remove a user from a group')
    parser_remove_user_group.add_argument('username', help='username of user')
    parser_remove_user_group.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_remove_user_group.set_defaults(func=remove_user_group)
    parser_modify = subparsers.add_parser('modify', help='modify an existing group')
    parser_modify.add_argument('group_path', help='group path (/parentA/parentB/name)')
    parser_modify.add_argument('--new-group-name', metavar='NAME', help='change group name')
    parser_modify.add_argument('attrs', nargs=argparse.REMAINDER,
                               help='space-separated NAME=VALUE attribute pairs. '
                                    'To delete NAME, omit VALUE. '
                                    'To make a list, assign to NAME multiple times.')
    parser_modify.set_defaults(func=modify_group)
    args = vars(parser.parse_args())

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rest_client = get_rest_client()
    func = args.pop('func')
    if 'attrs' in args:
        attrs = defaultdict(list)
        for item in args['attrs']:
            k,v = item.split('=', 1)
            if (attrs[k] and not v) or (attrs[k] is None and v):
                raise Exception('cannot assign to attr and leave it empty')
            elif v:
                attrs[k].append(v)  # keycloak stores all attributes as lists
            else:
                attrs[k] = None
        args['attrs'] = attrs
    ret = asyncio.run(func(rest_client=rest_client, **args))
    if ret is not None:
        pprint(ret)


if __name__ == '__main__':
    main()
