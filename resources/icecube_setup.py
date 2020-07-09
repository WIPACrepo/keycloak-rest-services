import os
import sys
import argparse

import requests

sys.path.append(os.getcwd())

from krs.apps import app_info
from krs.bootstrap import bootstrap
from krs.groups import create_group
from krs.token import get_token
from krs.util import config, ConfigRequired


def user_mgmt_app(appurl, token):
    cfg = config({
        'realm': ConfigRequired,
        'keycloak_url': ConfigRequired,
    })

    appname = 'user_mgmt'

    url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/clients?clientId={appname}'
    r = requests.get(url, headers={'Authorization': f'bearer {token}'})
    r.raise_for_status()
    ret = r.json()

    if ret:
        print('user_mgmt app already exists')
    else:
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/clients'
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
            'directAccessGrantsEnabled': False,
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

        ret = app_info(appname, token=token)
        client_id = ret['id']
        
        url = f'{cfg["keycloak_url"]}/auth/admin/realms/{cfg["realm"]}/clients/{client_id}/protocol-mappers/models'
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
        
        print('user_mgmt app created')


def main():
    parser = argparse.ArgumentParser(description='IceCube Keycloak setup')
    parser.add_argument('keycloak_url', help='Keycloak url')
    parser.add_argument('user_mgmt_url', help='User Management url')
    parser.add_argument('-u','--username', default='admin', help='admin username')
    parser.add_argument('-p','--password', default='admin', help='admin password')

    args = parser.parse_args()

    os.environ['realm'] = 'IceCube'
    os.environ['keycloak_url'] = args.keycloak_url
    os.environ['username'] = args.username
    os.environ['password'] = args.password

    # set up realm and REST API
    secret = bootstrap()
    os.environ['client_id'] = 'rest-access'
    os.environ['client_secret'] = secret
    token = get_token()

    # set up basic group structure
    g = {
        'institutions': {
            'IceCube': {},
            'IceCube-Gen2': {},
            'HAWC': {},
            'CTA': {},
            'ARA': {},
        },
        'experiments': {
            'IceCube': {
                'Working Groups': {},
            },
        },
        'posix': {},
        'tokens': {},
    }
    def create_subgroups(root, values):
        for name in values:
            groupname = root+'/'+name
            create_group(groupname, token=token)
            if values[name]:
                create_subgroups(groupname, values[name])
    create_subgroups('', g)

    # set up user_mgmt app
    user_mgmt_app(args.user_mgmt_url, token)


if __name__ == '__main__':
    main()
