"""
Group actions against Keycloak.
"""
import asyncio

from rest_tools.client import RestClient

from .users import user_info
from .util import config, ConfigRequired

async def list_groups(token=None):
    """
    List groups in Keycloak.

    Returns:
        dict: groupname: group details
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
        'max_groups': 10000,
    })
    url = f'/auth/admin/realms/{cfg["realm"]}/groups?max={cfg["max_groups"]}'
    r = RestClient(cfg["keycloak_url"], token=token)
    group_hierarchy = await r.request('GET', url)
    ret = {}
    def add_groups(groups):
        for g in groups:
            ret[g['path']] = {
                'id': g['id'],
                'name': g['name'],
                'path': g['path'],
                'children': [gg['name'] for gg in g['subGroups']],
            }
            if g['subGroups']:
                add_groups(g['subGroups'])
    add_groups(group_hierarchy)
    return ret

async def group_info(group_path, token=None):
    """
    Get group information.

    Args:
        group_path (str): group path (/parent/parent/name)

    Returns:
        dict: group info
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = await list_groups(token=token)
    if group_path not in groups:
        raise Exception(f'group "{group_path}" does not exist')

    group_id = groups[group_path]['id']

    url = f'/auth/admin/realms/{cfg["realm"]}/groups/{group_id}'
    r = RestClient(cfg["keycloak_url"], token=token)
    ret = await r.request('GET', url)

    if not ret:
        raise Exception(f'group "{group_path}" does not exist')
    return ret

async def create_group(group_path, token=None):
    """
    Create a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = await list_groups(token=token)
    if group_path in groups:
        print(f'group "{group_path}" already exists')
    else:
        if '/' not in group_path:
            raise Exception('"group_path" must start with /')
        parent,groupname = group_path.rsplit('/',1)
        if parent:
            if parent not in groups:
                raise Exception(f'parent group {parent} does not exist')
            parent_id = groups[parent]['id']
            url = f'/auth/admin/realms/{cfg["realm"]}/groups/{parent_id}/children'
        else:
            url = f'/auth/admin/realms/{cfg["realm"]}/groups'
        
        print(f'creating group "{group_path}"')
        group = {
            'name': groupname,
        }
        r = RestClient(cfg["keycloak_url"], token=token)
        await r.request('POST', url, group)
        print(f'group "{group_path}" created')

async def delete_group(group_path, token=None):
    """
    Delete a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = await list_groups(token=token)
    if group_path in groups:
        url = f'/auth/admin/realms/{cfg["realm"]}/groups/{groups[group_path]["id"]}'
        r = RestClient(cfg["keycloak_url"], token=token)
        await r.request('DELETE', url)
        print(f'group "{group_path}" deleted')
    else:
        print(f'group "{group_path}" does not exist')

async def get_group_membership(group_path, token=None):
    """
    Get the membership list of a group.

    Args:
        group_path (str): group path (/parent/parent/name)

    Returns:
        list: group paths
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = await list_groups(token=token)
    if group_path not in groups:
        raise Exception(f'group "{group_path}" does not exist')
    group_id = groups[group_path]['id']

    url = f'/auth/admin/realms/{cfg["realm"]}/groups/{group_id}/members'
    r = RestClient(cfg["keycloak_url"], token=token)
    data = await r.request('GET', url)

    ret = []
    for user in data:
        ret.append(user['username'])
    return ret

async def get_user_groups(username, token=None):
    """
    Get the groups a user has membership in.

    Args:
        username (str): username of user

    Returns:
        list: group paths
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    info = await user_info(username, token=token)

    url = f'/auth/admin/realms/{cfg["realm"]}/users/{info["id"]}/groups'
    r = RestClient(cfg["keycloak_url"], token=token)
    data = await r.request('GET', url)

    ret = []
    for g in data:
        ret.append(g['path'])
    return ret

async def add_user_group(group_path, username, token=None):
    """
    Add a user to a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
        username (str): username of user
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = await list_groups(token=token)
    if group_path not in groups:
        raise Exception(f'group "{group_path}" does not exist')

    info = await user_info(username, token=token)
    membership = await get_user_groups(username, token=token)

    if group_path in membership:
        print(f'user "{username}" already a member of group "{group_path}"')
    else:
        url = f'/auth/admin/realms/{cfg["realm"]}/users/{info["id"]}/groups/{groups[group_path]["id"]}'
        r = RestClient(cfg["keycloak_url"], token=token)
        await r.request('PUT', url)
        print(f'user "{username}" added to group "{group_path}"')

async def remove_user_group(group_path, username, token=None):
    """
    Remove a user from a group in Keycloak.

    Args:
        group_path (str): group path (/parent/parent/name)
        username (str): username of user
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = await list_groups(token=token)
    if group_path not in groups:
        raise Exception(f'group "{group_path}" does not exist')

    info = await user_info(username, token=token)
    membership = await get_user_groups(username, token=token)

    if group_path not in membership:
        print(f'user "{username}" not a member of group "{group_path}"')
    else:
        url = f'/auth/admin/realms/{cfg["realm"]}/users/{info["id"]}/groups/{groups[group_path]["id"]}'
        r = RestClient(cfg["keycloak_url"], token=token)
        await r.request('DELETE', url)
        print(f'user "{username}" removed from group "{group_path}"')

def main():
    import argparse
    from pprint import pprint
    from .token import get_token

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
    args = parser.parse_args()

    token = get_token()

    args = vars(args)
    func = args.pop('func')
    ret = asyncio.run(func(token=token, **args))
    if ret is not None:
        pprint(ret)

if __name__ == '__main__':
    main()