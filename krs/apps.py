"""
Managing applications ("clients") in Keycloak.

App structure:

1. Keycloak client
  - access type = confidential
    - can only get tokens through the app
  - roles:
    - can be tied to groups or individual users
  - scopes:
    - can be a list of other app scopes available
    - default available scopes:
      - "profile" - username, name, groups
      - "email" - email
      - "institution" - institution
2. Keycloak client scope
  - same name as client
  - when selected, puts the app roles into the token

Also available: a generic "public" app for public access to scopes,
if the application scope is allowed to be public.
"""
import os
import asyncio
import logging

import requests

from .token import get_rest_client
from .groups import list_groups, group_info


logger = logging.getLogger('krs.apps')


async def list_apps(rest_client=None):
    """
    List applications ("clients") in Keycloak.

    Returns:
        dict: app name: app info
    """
    url = '/clients'
    clients = await rest_client.request('GET', url)
    ret = {}
    for c in clients:
        if 'app' not in c['attributes'] or not c['attributes']['app']:
            continue
        ret[c['clientId']] = {k: c[k] for k in c if k in ('clientId', 'defaultClientScopes', 'id', 'optionalClientScopes', 'rootUrl', 'serviceAccountsEnabled')}
    return ret


async def app_info(appname, rest_client=None):
    """
    Get application ("client") information.

    Args:
        appname (str): app name ("clientID")

    Returns:
        dict: app info
    """
    url = f'/clients?clientId={appname}'
    ret = await rest_client.request('GET', url)

    if not ret:
        raise Exception(f'app "{appname}" does not exist')
    data = ret[0]

    url = f'/clients/{data["id"]}/client-secret'
    ret = await rest_client.request('GET', url)
    if 'value' in ret:
        data['clientSecret'] = ret['value']

    url = f'/clients/{data["id"]}/roles'
    ret = await rest_client.request('GET', url)
    data['roles'] = [r['name'] for r in ret]

    return data


async def list_scopes(only_apps=True, mappers=False, rest_client=None):
    """
    List scopes in Keycloak.

    Args:
        only_apps (bool): only list app scopes (default True)
        mappers (bool): list mappers (default False)

    Returns:
        dict: scope name: info
    """
    url = '/client-scopes'
    scopes = await rest_client.request('GET', url)
    ret = {}
    for s in scopes:
        if s['protocol'] != 'openid-connect':
            continue
        if only_apps and 'app' not in s['attributes']:
            continue
        ret[s['name']] = {k: s[k] for k in s if k in ('id', 'name', 'attributes')}
        if mappers and 'protocolMappers' in s:
            ret[s['name']]['protocolMappers'] = s['protocolMappers']
    return ret


async def create_app(appname, appurl, roles=['read', 'write'], builtin_scopes=[], access='public', service_account=False, rest_client=None):
    """
    Create an application ("client") in Keycloak.

    Args:
        appname (str): appname ("clientId") of application to create
        appurl (str): base url of app
        roles (list): roles of app
        builtin_scopes (list): builtin Keycloak scopes to allow (profile, email, institution) (default: none)
        access (str): app scope access to roles (public, apps, none) (default: public)
        service_account (bool): enable the service account (default: False)
    """
    if access not in ('public', 'apps', 'none'):
        raise Exception('access is not one of the options: ["public", "apps", "none"]')
    if any(True for s in builtin_scopes if s not in ('profile', 'email', 'institution')):
        raise Exception('builtin_scopes has invalid scope. options are ["profile", "email", "institution"]')
    if not appurl.startswith('http'):
        raise Exception('bad appurl')

    # create app
    try:
        await app_info(appname, rest_client=rest_client)
    except Exception:
        logger.info(f'creating app "{appname}"')
        args = {
            'access': {'configure': True, 'manage': True, 'view': True},
            'adminUrl': appurl,
            'attributes': {
                'app': 'true',
                'display.on.consent.screen': 'false',
                'exclude.session.state.from.auth.response': 'false',
                'saml.assertion.signature': 'false',
                'saml.authnstatement': 'false',
                'saml.client.signature': 'false',
                'saml.encrypt': 'false',
                'saml.force.post.binding': 'false',
                'saml.multivalued.roles': 'false',
                'saml.onetimeuse.condition': 'false',
                'saml.server.signature': 'false',
                'saml.server.signature.keyinfo.ext': 'false',
                'saml_force_name_id_format': 'false',
                'tls.client.certificate.bound.access.tokens': 'false',
            },
            'authenticationFlowBindingOverrides': {},
            'bearerOnly': False,
            'clientAuthenticatorType': 'client-secret',
            'clientId': appname,
            'consentRequired': True,
            'defaultClientScopes': [],
            'directAccessGrantsEnabled': False,
            'enabled': True,
            'frontchannelLogout': False,
            'fullScopeAllowed': True,
            'implicitFlowEnabled': False,
            'nodeReRegistrationTimeout': -1,
            'notBefore': 0,
            'optionalClientScopes': [],
            'protocol': 'openid-connect',
            'publicClient': False,
            'redirectUris': [f'{appurl}/*'],
            'rootUrl': appurl,
            'serviceAccountsEnabled': service_account,
            'standardFlowEnabled': True,
            'surrogateAuthRequired': False,
            'webOrigins': [appurl],
        }
        await rest_client.request('POST', '/clients', args)

        ret = await app_info(appname, rest_client=rest_client)
        client_id = ret['id']

        # create roles
        url = f'/clients/{client_id}/roles'
        for name in roles:
            args = {'name': name}
            await rest_client.request('POST', url, args)

        # create scope
        all_scopes = await list_scopes(rest_client=rest_client)
        if appname not in all_scopes:
            args = {
                'attributes': {
                    'app': 'app',
                    'access': access,
                    'display.on.consent.screen': 'false',
                    'include.in.token.scope': 'true',
                },
                'name': appname,
                'protocol': 'openid-connect',
            }
            await rest_client.request('POST', '/client-scopes', args)
            all_scopes = await list_scopes(rest_client=rest_client)
            scope_id = all_scopes[appname]['id']

            url = f'/client-scopes/{scope_id}/protocol-mappers/models'
            args = {
                'config': {
                    'access.token.claim': 'true',
                    'claim.name': f'roles.{appname}',
                    'id.token.claim': 'false',
                    'jsonType.label': 'String',
                    'multivalued': 'true',
                    'userinfo.token.claim': 'false',
                    'usermodel.clientRoleMapping.clientId': appname,
                },
                'name': 'role-mapper',
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-usermodel-client-role-mapper'
            }
            await rest_client.request('POST', url, args)

        # apply scope to client
        scope_id = all_scopes[appname]['id']
        url = f'/clients/{client_id}/optional-client-scopes/{scope_id}'
        await rest_client.request('PUT', url)

        if access == 'public':
            # apply scope to "public" app
            ret = await app_info("public", rest_client=rest_client)
            url = f'/clients/{ret["id"]}/optional-client-scopes/{scope_id}'
            await rest_client.request('PUT', url)
        if access in ('public', 'apps'):
            # apply scope to all "apps"
            ret = await list_apps(rest_client=rest_client)
            for app in ret.values():
                if appname not in app['optionalClientScopes']:
                    url = f'/clients/{app["id"]}/optional-client-scopes/{scope_id}'
                    await rest_client.request('PUT', url)

        if service_account:
            # get service account
            url = f'/clients/{client_id}/service-account-user'
            svc_user = await rest_client.request('GET', url)

            # get service roles
            url = f'/users/{svc_user["id"]}/role-mappings/clients/{client_id}'
            svc_roles = await rest_client.request('GET', url)

            for role in svc_roles:
                if role['name'] == 'uma_authorization':  # delete this to prevent self-administration
                    url = f'/users/{svc_user["id"]}/role-mappings/clients/{client_id}'
                    await rest_client.request('DELETE', url)

        logger.info(f'app "{appname}" created')
    else:
        logger.info(f'app "{appname}" already exists')


async def delete_app(appname, rest_client=None):
    """
    Delete an application ("client") in Keycloak.

    Args:
        appname (str): appname ("clientId') of application to delete
    """
    ret = await list_scopes(rest_client=rest_client)
    if appname in ret:
        scope_id = ret[appname]['id']
        # delete scope usage in apps
        apps = await list_apps(rest_client=rest_client)
        for app in apps.values():
            if appname in app['optionalClientScopes']:
                url = f'/clients/{app["id"]}/optional-client-scopes/{scope_id}'
                await rest_client.request('DELETE', url)
        ret = await app_info('public', rest_client=rest_client)
        if appname in ret['optionalClientScopes']:
            url = f'/clients/{ret["id"]}/optional-client-scopes/{scope_id}'
            await rest_client.request('DELETE', url)

        # delete scope
        url = f'/client-scopes/{scope_id}'
        await rest_client.request('DELETE', url)

    try:
        ret = await app_info(appname, rest_client=rest_client)
    except Exception:
        logger.info(f'app "{appname}" does not exist')
    else:
        client_id = ret['id']
        url = f'/clients/{client_id}'
        await rest_client.request('DELETE', url)
        logger.info(f'app "{appname}" deleted')


async def get_app_role_mappings(appname, role=None, rest_client=None):
    """
    Get an application's role-group mappings.

    Args:
        appname (str): appname ("clientId") of application
        role (str): application role name (optional, default: all roles)

    Returns:
        dict: role: list of groups
    """
    try:
        app_data = await app_info(appname, rest_client=rest_client)
    except Exception:
        raise Exception(f'app "{appname}" does not exist')

    if role and role not in app_data['roles']:
        raise Exception(f'role "{role}" does not exist in app "{appname}"')

    client_id = app_data['id']

    groups_with_role = {}
    groups = await list_groups(rest_client=rest_client)
    for g in groups:
        gid = groups[g]['id']

        url = f'/groups/{gid}/role-mappings/clients/{client_id}'
        ret = await rest_client.request('GET', url)
        for mapping in ret:
            role_name = mapping['name']
            if (not role) or role == role_name:
                if role_name in groups_with_role:
                    groups_with_role[role_name].append(g)
                else:
                    groups_with_role[role_name] = [g]
    return groups_with_role


async def add_app_role_mapping(appname, role, group, rest_client=None):
    """
    Add a role-group mapping to an application.

    Args:
        appname (str): appname ("clientId") of application
        role (str): application role name
        group (str): group name
    """
    try:
        app_data = await app_info(appname, rest_client=rest_client)
    except Exception:
        raise Exception(f'app "{appname}" does not exist')

    if role not in app_data['roles']:
        raise Exception(f'role "{role}" does not exist in app "{appname}"')

    gid = (await group_info(group, rest_client=rest_client))['id']
    client_id = app_data['id']

    url = f'/groups/{gid}/role-mappings/clients/{client_id}'
    mappings = await rest_client.request('GET', url)
    if any(role == mapping['name'] for mapping in mappings):
        logger.info(f'app "{appname}" role mapping {role}-{group} already exists')
    else:
        # get full role info
        url = f'/clients/{client_id}/roles'
        roles = await rest_client.request('GET', url)
        for entry in roles:
            if entry['name'] == role:
                role_info = entry
                break
        else:
            raise Exception('could not get role representation')

        url = f'/groups/{gid}/role-mappings/clients/{client_id}'
        args = [role_info]
        await rest_client.request('POST', url, args)
        logger.info(f'app "{appname}" role mapping {role}-{group} created')


async def delete_app_role_mapping(appname, role, group, rest_client=None):
    """
    Delete a role-group mapping to an application.

    Args:
        appname (str): appname ("clientId") of application
        role (str): application role name
        group (str): group path
    """
    try:
        app_data = await app_info(appname, rest_client=rest_client)
    except Exception:
        raise Exception(f'app "{appname}" does not exist')

    if role not in app_data['roles']:
        raise Exception(f'role "{role}" does not exist in app "{appname}"')

    gid = (await group_info(group, rest_client=rest_client))['id']
    client_id = app_data['id']

    url = f'/groups/{gid}/role-mappings/clients/{client_id}'
    mappings = await rest_client.request('GET', url)
    if not any(role == mapping['name'] for mapping in mappings):
        logger.info(f'app "{appname}" role mapping {role}-{group} does not exist')
    else:
        # get full role info
        url = f'/clients/{client_id}/roles'
        roles = await rest_client.request('GET', url)
        for entry in roles:
            if entry['name'] == role:
                role_info = entry
                break
        else:
            raise Exception('could not get role representation')

        url = f'/groups/{gid}/role-mappings/clients/{client_id}'
        args = [role_info]
        await rest_client.request('DELETE', url, args)
        logger.info(f'app "{appname}" role mapping {role}-{group} deleted')


def get_public_token(username, password, scopes=None, openid_url=None, client='public', secret=None, raw=False, **kwargs):
    import jwt
    import json

    if not scopes:
        scopes = []

    if password is None:
        # get password from cmdline
        import getpass
        password = getpass.getpass()

    # discovery
    r = requests.get(os.path.join(openid_url, '.well-known/openid-configuration'))
    r.raise_for_status()
    provider_info = r.json()

    # get keys
    r = requests.get(provider_info['jwks_uri'])
    r.raise_for_status()
    public_keys = {}
    for jwk in r.json()['keys']:
        kid = jwk['kid']
        public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    def decode(encoded):
        header = jwt.get_unverified_header(encoded)
        if header['kid'] in public_keys:
            key = public_keys[header['kid']]
            return jwt.decode(encoded, key, algorithms=['RS256', 'RS512'], options={'verify_aud': False})
        else:
            raise Exception('key not found')

    # actually get an access token
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        # 'audience': api_identifier,
        'scope': ' '.join(scopes),
        'client_id': client,
    }
    if secret:
        data['client_secret'] = secret
    r = requests.post(provider_info['token_endpoint'], data=data)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            logger.info('Error:', e.response.json()['error_description'])
        except Exception:
            pass
        raise
    tokens = r.json()

    if raw:
        return tokens['access_token']
    else:
        return decode(tokens['access_token'])


def main():
    import argparse
    from pprint import pprint
    from wipac_dev_tools import from_environment

    parser = argparse.ArgumentParser(description='Keycloak application management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list apps')
    parser_list.set_defaults(func=list_apps)
    parser_info = subparsers.add_parser('info', help='app info')
    parser_info.add_argument('appname', help='application name')
    parser_info.set_defaults(func=app_info)
    parser_list_scopes = subparsers.add_parser('list_scopes', help='list scopes')
    parser_list_scopes.add_argument('--include-builtin', dest='only_apps', action='store_false', default=True, help='include builtin Keycloak scopes')
    parser_list_scopes.add_argument('--mappers', action='store_true', help='include mappers')
    parser_list_scopes.set_defaults(func=list_scopes)
    parser_create = subparsers.add_parser('create', help='create a new app')
    parser_create.add_argument('appname', help='application name')
    parser_create.add_argument('appurl', help='app base url')
    parser_create.set_defaults(func=create_app)
    parser_delete = subparsers.add_parser('delete', help='delete an app')
    parser_delete.add_argument('appname', help='application name')
    parser_delete.set_defaults(func=delete_app)
    parser_get_role_mappings = subparsers.add_parser('get_role_mappings', help='get app role-group mappings')
    parser_get_role_mappings.add_argument('appname', help='application name')
    parser_get_role_mappings.add_argument('-r', '--role', help='role name')
    parser_get_role_mappings.set_defaults(func=get_app_role_mappings)
    parser_add_role_mapping = subparsers.add_parser('add_role_mapping', help='add an app role-group mapping')
    parser_add_role_mapping.add_argument('appname', help='application name')
    parser_add_role_mapping.add_argument('role', help='role name')
    parser_add_role_mapping.add_argument('group', help='group path')
    parser_add_role_mapping.set_defaults(func=add_app_role_mapping)
    parser_delete_role_mapping = subparsers.add_parser('delete_role_mapping', help='delete an app role-group mapping')
    parser_delete_role_mapping.add_argument('appname', help='application name')
    parser_delete_role_mapping.add_argument('role', help='role name')
    parser_delete_role_mapping.add_argument('group', help='group path')
    parser_delete_role_mapping.set_defaults(func=delete_app_role_mapping)
    parser_get_public_token = subparsers.add_parser('get_public_token', help='get a user token')
    parser_get_public_token.add_argument('username', help='username of user')
    parser_get_public_token.add_argument('--password', default=None, help='password of user')
    parser_get_public_token.add_argument('-s', '--scopes', action='append', help='app scopes to request')
    parser_get_public_token.add_argument('--client', default='public', help='app (client) to request')
    parser_get_public_token.add_argument('--secret', help='app (client) secret (if necessary)')
    parser_get_public_token.add_argument('--raw', action='store_true', help='output raw token')
    parser_get_public_token.set_defaults(func=get_public_token)
    args = vars(parser.parse_args())

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rest_client = get_rest_client()
    func = args.pop('func')
    if func == get_public_token:
        config = from_environment({
            'KEYCLOAK_REALM': None,
            'KEYCLOAK_URL': None,
        })
        args['openid_url'] = f'{config["KEYCLOAK_URL"]}/auth/realms/{config["KEYCLOAK_REALM"]}'
        ret = func(**args)
    else:
        ret = asyncio.run(func(rest_client=rest_client, **args))
    if ret is not None:
        pprint(ret)


if __name__ == '__main__':
    main()
