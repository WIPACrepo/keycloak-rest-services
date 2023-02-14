"""
Bootstrap a Keycloak instance with an admin role account for REST access.
"""
import time
import requests

from wipac_dev_tools import from_environment


def wait_for_keycloak(timeout=300):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    url = f'{cfg["KEYCLOAK_URL"]}/auth/'
    start_time = time.time()
    while True:
        try:
            r = requests.get(url)
            r.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if start_time + timeout > time.time():
                time.sleep(1)
                continue
            raise Exception('Keycloak did not start') from e


def get_token():
    cfg = from_environment({
        'KEYCLOAK_URL': None,
        'USERNAME': None,
        'PASSWORD': None,
    })
    url = f'{cfg["KEYCLOAK_URL"]}/auth/realms/master/protocol/openid-connect/token'
    args = {
        'client_id': 'admin-cli',
        'grant_type': 'password',
        'username': cfg['USERNAME'],
        'password': cfg['PASSWORD'],
    }

    r = requests.post(url, data=args)
    r.raise_for_status()
    req = r.json()
    return req['access_token']


def create_realm(realm, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    try:
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}'
        r = requests.get(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f'creating realm "{realm}"')
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/'
        r = requests.post(url, json={'realm': realm, 'enabled': True},
                          headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'realm "{realm}" created')
    else:
        print(f'realm "{realm}" already exists')


def delete_realm(realm, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    try:
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}'
        r = requests.get(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f'realm "{realm}" does not exist')
    else:
        print(f'deleting realm "{realm}"')
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'realm "{realm}" deleted')


def create_service_role(client_id, realm=None, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    clients = r.json()

    # get realm client id for later
    realm_client = None
    for c in clients:
        if c['clientId'] == f'{realm}-realm':
            realm_client = c['id']
            break
    else:
        raise Exception(f'realm {realm} not created yet')

    if not any(c['clientId'] == client_id for c in clients):
        print(f'creating client "{client_id}"')
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients'
        args = {
            'authorizationServicesEnabled': False,
            'clientId': client_id,
            'consentRequired': False,
            'defaultClientScopes': ['web-origins', 'roles'],
            'directAccessGrantsEnabled': True,
            'enabled': True,
            'fullScopeAllowed': True,
            'implicitFlowEnabled': False,
            'optionalClientScopes': ['offline_access', 'microprofile-jwt'],
            'serviceAccountsEnabled': True,
            'standardFlowEnabled': False,
        }
        r = requests.post(url, json=args,
                          headers={'Authorization': f'bearer {token}'})
        try:
            r.raise_for_status()
        except Exception:
            print(r.text)
            raise

        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients'
        r = requests.get(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        clients = r.json()
        if not any(c['clientId'] == client_id for c in clients):
            raise Exception(f'failed to create client {client_id}')
        print(f'created client "{client_id}"')
    else:
        print(f'client "{client_id}" already exists')

    kc_id = None
    for c in clients:
        if c['clientId'] == client_id:
            kc_id = c['id']
            break

    # get service account
    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients/{kc_id}/service-account-user'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    svc_user = r.json()

    # get roles available
    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/users/{svc_user["id"]}/role-mappings/clients/{realm_client}/available'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    roles = r.json()

    client_roles = []
    for r in roles:
        if r['name'] in ('create-client', 'manage-clients', 'manage-users', 'query-clients', 'view-clients', 'view-users', 'view-realm'):
            client_roles.append(r)

    if client_roles:
        print('service account roles to add:', client_roles)
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/users/{svc_user["id"]}/role-mappings/clients/{realm_client}'
        r = requests.post(url, json=client_roles, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()

    # get service account secret
    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients/{kc_id}/client-secret'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    if 'value' not in r.json():
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients/{kc_id}/client-secret'
        r = requests.post(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
    return r.json()['value']


def delete_service_role(client_id, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    clients = r.json()

    # get actual system id
    system_id = None
    for c in clients:
        if c['clientId'] == client_id:
            system_id = c['id']
            break

    if not system_id:
        print(f'client "{client_id}" does not exist')
    else:
        print(f'deleting client "{client_id}"')
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/master/clients/{system_id}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        try:
            r.raise_for_status()
        except Exception:
            print(r.text)
            raise


def create_public_app(realm=None, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    appname = 'public'
    appurl = ''

    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}/clients?clientId={appname}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = r.json()

    if ret:
        print('public app already exists')
    else:
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}/clients'
        args = {
            'access': {'configure': True, 'manage': True, 'view': True},
            'adminUrl': appurl,
            'attributes': {
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
            'consentRequired': False,
            'defaultClientScopes': [],
            'directAccessGrantsEnabled': True,
            'enabled': True,
            'frontchannelLogout': False,
            'fullScopeAllowed': True,
            'implicitFlowEnabled': False,
            'nodeReRegistrationTimeout': -1,
            'notBefore': 0,
            'optionalClientScopes': ['profile'],
            'protocol': 'openid-connect',
            'publicClient': True,
            'redirectUris': [f'{appurl}/*'],
            'serviceAccountsEnabled': False,
            'standardFlowEnabled': False,
            'surrogateAuthRequired': False,
            'webOrigins': [],
        }
        r = requests.post(url, json=args, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print('public app created')


def user_mgmt_app(appurl, passwordGrant=False, token=None):
    """
    Create the user management client in Keycloak.

    Args:
        appurl (str): url where app is deployed
        passwordGrant (bool): (optional) whether to allow password grands (default: False)
        token (str): admin rest api token
    """
    cfg = from_environment({
        'KEYCLOAK_URL': None,
        'KEYCLOAK_REALM': None,
    })

    appname = 'user_mgmt'

    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{cfg["KEYCLOAK_REALM"]}/clients?clientId={appname}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = r.json()

    if ret:
        print('user_mgmt app already exists')
    else:
        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{cfg["KEYCLOAK_REALM"]}/clients'
        args = {
            'access': {'configure': True, 'manage': True, 'view': True},
            'adminUrl': appurl,
            'attributes': {},
            'authenticationFlowBindingOverrides': {},
            'bearerOnly': False,
            'clientAuthenticatorType': 'client-secret',
            'clientId': appname,
            'consentRequired': False,
            'defaultClientScopes': ['profile', 'email'],
            'directAccessGrantsEnabled': passwordGrant,
            'enabled': True,
            'frontchannelLogout': False,
            'fullScopeAllowed': True,
            'implicitFlowEnabled': False,
            'nodeReRegistrationTimeout': -1,
            'notBefore': 0,
            'optionalClientScopes': [],
            'protocol': 'openid-connect',
            'publicClient': True,
            'redirectUris': [f'{appurl}/*'],
            'rootUrl': appurl,
            'serviceAccountsEnabled': False,
            'standardFlowEnabled': True,
            'surrogateAuthRequired': False,
            'webOrigins': [appurl],
        }
        r = requests.post(url, json=args, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()

        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{cfg["KEYCLOAK_REALM"]}/clients?clientId={appname}'
        r = requests.get(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        ret = r.json()
        if not ret:
            raise Exception('failed to create user_mgmt_app')
        client_id = ret[0]['id']

        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{cfg["KEYCLOAK_REALM"]}/clients/{client_id}/protocol-mappers/models'
        args = {
            'config': {
                'access.token.claim': 'true',
                'claim.name': 'groups',
                'full.path': 'true',
                'userinfo.token.claim': 'true',
            },
            'consentRequired': False,
            'name': 'groups',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-group-membership-mapper',
        }
        r = requests.post(url, json=args, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()

        url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{cfg["KEYCLOAK_REALM"]}/clients/{client_id}/protocol-mappers/models'
        args = {
            'config': {
                'access.token.claim': 'true',
                'claim.name': 'username',
                'id.token.claim': 'true',
                'jsonType.label': 'String',
                'user.attribute': 'username',
                'userinfo.token.claim': 'true',
            },
            'consentRequired': False,
            'name': 'username',
            'protocol': 'openid-connect',
            'protocolMapper': 'oidc-usermodel-property-mapper',
        }
        r = requests.post(url, json=args, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()

        print('user_mgmt app created')


def add_rabbitmq_listener(realm=None, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}/events/config'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    event_config = r.json()

    # make sure rabbitmq is in the config listeners
    if 'keycloak-to-rabbitmq' in event_config['eventsListeners']:
        print('rabbitmq listener already registered')
    else:
        print('registering rabbitmq listener')
        event_config['eventsListeners'].append('keycloak-to-rabbitmq')
        r = requests.put(url, json=event_config, headers={'Authorization': f'bearer {token}'})
        try:
            r.raise_for_status()
        except Exception:
            print(r.text)
            raise


def add_custom_theme(realm=None, token=None):
    cfg = from_environment({
        'KEYCLOAK_URL': None,
    })

    url = f'{cfg["KEYCLOAK_URL"]}/auth/admin/realms/{realm}/'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    main_config = r.json()

    # make sure theme is selected
    if main_config.get('loginTheme', '') == 'custom':
        print('custom theme already registered')
    else:
        print('registering custom theme')
        main_config['loginTheme'] = 'custom'
        r = requests.put(url, json=main_config, headers={'Authorization': f'bearer {token}'})
        try:
            r.raise_for_status()
        except Exception:
            print(r.text)
            raise


def bootstrap():
    cfg = from_environment({
        'KEYCLOAK_REALM': None,
        'KEYCLOAK_CLIENT_ID': 'rest-access',
    })

    wait_for_keycloak()

    for i in range(3):
        try:
            token = get_token()
        except requests.exceptions.HTTPError:
            if i < 2:
                continue
            raise
        break

    print('Keycloak token obtained, setting up...')

    create_realm(cfg['KEYCLOAK_REALM'], token=token)

    create_public_app(cfg['KEYCLOAK_REALM'], token=token)

    client_secret = create_service_role(cfg['KEYCLOAK_CLIENT_ID'], realm=cfg['KEYCLOAK_REALM'], token=token)

    # add_rabbitmq_listener(realm=cfg['KEYCLOAK_REALM'], token=token)

    # add_custom_theme(realm=cfg['KEYCLOAK_REALM'], token=token)

    print(f'\nclient_id={cfg["KEYCLOAK_CLIENT_ID"]}')
    print(f'client_secret={client_secret}')
    return client_secret


if __name__ == '__main__':
    bootstrap()
