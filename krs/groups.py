"""
Group actions against KeyCloak.
"""
import requests

from .util import config, ConfigRequired

def list_groups(token=None):
    """
    List groups in KeyCloak.

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

def create_group(groupname, parent=None, token=None):
    """
    Create a group in KeyCloak.

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
    Delete a group in KeyCloak.

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

def main():
    import argparse
    from pprint import pprint
    from .token import get_token

    parser = argparse.ArgumentParser(description='KeyCloak group management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list groups')
    parser_list.set_defaults(func=list_groups)
    parser_create = subparsers.add_parser('create', help='create a new group')
    parser_create.add_argument('-p','--parent', help='group parent')
    parser_create.add_argument('groupname', help='group name')
    parser_create.set_defaults(func=create_group)
    parser_delete = subparsers.add_parser('delete', help='delete a group')
    parser_delete.add_argument('groupname', help='group name')
    parser_delete.set_defaults(func=delete_group)
    args = parser.parse_args()

    token = get_token()

    args = vars(args)
    func = args.pop('func')
    ret = func(token=token, **args)
    if ret:
        pprint(ret)

if __name__ == '__main__':
    main()