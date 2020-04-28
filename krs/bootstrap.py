"""
Bootstrap a Keycloak instance with an admin role account for REST access.
"""
import time
import requests

from .util import config, ConfigRequired


def wait_for_keycloak(timeout=300):
    cfg = config({
        'keycloak_url': ConfigRequired,
    })

    url = f'{cfg["keycloak_url"]}/auth/'
    for _ in range(timeout):
        try:
            r = requests.get(url)
            r.raise_for_status()
            break
        except requests.exceptions.RequestException:
            time.sleep(1)
    else:
        raise Exception('Keycloak did not start')

def get_token():
    if get_token.cache:
        return get_token.cache

    cfg = config({
        'keycloak_url': ConfigRequired,
        'username': ConfigRequired,
        'password': ConfigRequired,
    })
    url = f'{cfg["keycloak_url"]}/auth/realms/master/protocol/openid-connect/token'
    args = {
        'client_id': 'admin-cli',
        'grant_type': 'password',
        'username': cfg['username'],
        'password': cfg['password'],
    }

    r = requests.post(url, data=args)
    r.raise_for_status()
    req = r.json()
    get_token.cache = req['access_token']
    return get_token.cache
get_token.cache = None

def create_realm(realm, token=None):
    cfg = config({
        'keycloak_url': ConfigRequired,
    })

    try:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{realm}'
        r = requests.get(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f'creating realm "{realm}"')
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/'
        r = requests.post(url, json={'realm': realm},
                          headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'realm "{realm}" created')
    else:
        print(f'realm "{realm}" already exists')

def delete_realm(realm, token=None):
    cfg = config({
        'keycloak_url': ConfigRequired,
    })

    try:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{realm}'
        r = requests.get(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f'realm "{realm}" does not exist')
    else:
        print(f'deleting realm "{realm}"')
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{realm}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print(f'realm "{realm}" deleted')

def create_service_role(client_id, realm=None, token=None):
    cfg = config({
        'keycloak_url': ConfigRequired,
    })

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients'
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
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients'
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
        except:
            print(r.text)
            raise

        url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients'
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
    url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients/{kc_id}/service-account-user'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    svc_user = r.json()

    # get roles available
    url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/users/{svc_user["id"]}/role-mappings/clients/{realm_client}/available'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    roles = r.json()

    client_roles = []
    for r in roles:
        if r['name'] in ('create-client','manage-clients','manage-users','query-clients','view-clients','view-users','view-realm'):
            client_roles.append(r)

    if client_roles:
        print('service account roles to add:', client_roles)
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/users/{svc_user["id"]}/role-mappings/clients/{realm_client}'
        r = requests.post(url, json=client_roles, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()

    # get service account secret
    url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients/{kc_id}/client-secret'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    return r.json()['value']

def delete_service_role(client_id, token=None):
    cfg = config({
        'keycloak_url': ConfigRequired,
    })

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients'
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
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/master/clients/{system_id}'
        r = requests.delete(url, headers={'Authorization': f'bearer {token}'})
        try:
            r.raise_for_status()
        except:
            print(r.text)
            raise

def create_public_app(realm=None, token=None):
    cfg = config({
        'keycloak_url': ConfigRequired,
    })

    appname = 'public'
    appurl = ''

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{realm}/clients?clientId={appname}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = r.json()

    if ret:
        print('public app already exists')
    else:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{realm}/clients'
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
            'clientAuthenticatorType': 'public',
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
            'publicClient': False,
            'redirectUris': [f'{appurl}/*'],
            'rootUrl': appurl,
            'serviceAccountsEnabled': False,
            'standardFlowEnabled': False,
            'surrogateAuthRequired': False,
            'webOrigins': [appurl],
        }
        r = requests.post(url, json=args, headers={'Authorization': f'bearer {token}'})
        r.raise_for_status()
        print('public app created')

def bootstrap():
    cfg = config({
        'realm': ConfigRequired,
        'client_id': 'rest-access',
    })

    wait_for_keycloak()

    token = get_token()
    print('Keycloak token obtained, setting up...')

    create_realm(cfg['realm'], token=token)

    create_public_app(cfg['realm'], token=token)

    client_secret = create_service_role(cfg['client_id'], realm=cfg['realm'], token=token)

    print(f'\nclient_id={cfg["client_id"]}')
    print(f'client_secret={client_secret}')
    return client_secret

if __name__ == '__main__':
    bootstrap()