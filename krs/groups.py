"""
Group actions against Keycloak.
"""
import requests

from .users import user_info
from .util import config, ConfigRequired

def list_groups(token=None):
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
    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/groups?max={cfg["max_groups"]}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    group_hierarchy = r.json()
    ret = {}
    def add_groups(groups):
        for g in groups:
            ret[g['name']] = {
                'id': g['id'],
                'path': g['path'],
                'children': [gg['name'] for gg in g['subGroups']],
            }
            if g['subGroups']:
                add_groups(g['subGroups'])
    add_groups(group_hierarchy)
    return ret

def group_info(groupname, token=None):
    """
    Get group information.

    Args:
        groupname (str): group name

    Returns:
        dict: group info
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = list_groups(token=token)
    if groupname not in groups:
        raise Exception(f'group "{groupname}" does not exist')

    group_id = groups[groupname]['id']

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/groups/{group_id}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = r.json()

    if not ret:
        raise Exception(f'group "{groupname}" does not exist')
    return ret

def create_group(groupname, parent=None, token=None):
    """
    Create a group in Keycloak.

    Args:
        groupname (str): group name
        parent (str): (optional) parent group name if a sub-group
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = list_groups(token=token)
    if groupname in groups:
        print(f'group "{groupname}" already exists')
    else:
        if parent:
            if parent not in groups:
                raise Exception(f'parent group {parent} does not exist')
            parent_id = groups[parent]['id']
            url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/groups/{parent_id}/children'
        else:
            url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/groups'
        
        print(f'creating group "{groupname}"')
        group = {
            'name': groupname,
        }
        r = requests.post(url, json=group, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'group "{groupname}" created')

def delete_group(groupname, token=None):
    """
    Delete a group in Keycloak.

    Args:
        groupname (str): group name to delete
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = list_groups(token=token)
    if groupname in groups:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/groups/{groups[groupname]["id"]}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'group "{groupname}" deleted')
    else:
        print(f'group "{groupname}" does not exist')

def get_user_groups(username, token=None):
    """
    Get the groups a user has membership in.

    Args:
        username (str): username of user

    Returns:
        list: group names
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    info = user_info(username, token=token)

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users/{info["id"]}/groups'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()

    ret = []
    for g in r.json():
        ret.append(g['name'])
    return ret

def add_user_group(groupname, username, token=None):
    """
    Add a user to a group in Keycloak.

    Args:
        groupname (str): group name
        username (str): username of user
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = list_groups(token=token)
    if groupname not in groups:
        raise Exception(f'group "{groupname}" does not exist')

    info = user_info(username, token=token)
    membership = get_user_groups(username, token=token)

    if groupname in membership:
        print(f'user "{username}" already a member of group "{groupname}"')
    else:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users/{info["id"]}/groups/{groups[groupname]["id"]}'
        r = requests.put(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'user "{username}" added to group "{groupname}"')

def remove_user_group(groupname, username, token=None):
    """
    Remove a user from a group in Keycloak.

    Args:
        groupname (str): group name
        username (str): username of user
    """
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    groups = list_groups(token=token)
    if groupname not in groups:
        raise Exception(f'group "{groupname}" does not exist')

    info = user_info(username, token=token)
    membership = get_user_groups(username, token=token)

    if groupname not in membership:
        print(f'user "{username}" not a member of group "{groupname}"')
    else:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/users/{info["id"]}/groups/{groups[groupname]["id"]}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'user "{username}" removed from group "{groupname}"')

def main():
    import argparse
    from pprint import pprint
    from .token import get_token

    parser = argparse.ArgumentParser(description='Keycloak group management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list groups')
    parser_list.set_defaults(func=list_groups)
    parser_info = subparsers.add_parser('info', help='group info')
    parser_info.add_argument('groupname', help='group name')
    parser_info.set_defaults(func=group_info)
    parser_create = subparsers.add_parser('create', help='create a new group')
    parser_create.add_argument('-p','--parent', help='group parent')
    parser_create.add_argument('groupname', help='group name')
    parser_create.set_defaults(func=create_group)
    parser_delete = subparsers.add_parser('delete', help='delete a group')
    parser_delete.add_argument('groupname', help='group name')
    parser_delete.set_defaults(func=delete_group)
    parser_get_user_groups = subparsers.add_parser('get_user_groups', help="get a user's group memberships")
    parser_get_user_groups.add_argument('username', help='username of user')
    parser_get_user_groups.set_defaults(func=get_user_groups)
    parser_add_user_group = subparsers.add_parser('add_user_group', help='add a user to a group')
    parser_add_user_group.add_argument('username', help='username of user')
    parser_add_user_group.add_argument('groupname', help='group name')
    parser_add_user_group.set_defaults(func=add_user_group)
    parser_remove_user_group = subparsers.add_parser('remove_user_group', help='remove a user from a group')
    parser_remove_user_group.add_argument('username', help='username of user')
    parser_remove_user_group.add_argument('groupname', help='group name')
    parser_remove_user_group.set_defaults(func=remove_user_group)
    args = parser.parse_args()

    token = get_token()

    args = vars(args)
    func = args.pop('func')
    ret = func(token=token, **args)
    if ret is not None:
        pprint(ret)

if __name__ == '__main__':
    main()