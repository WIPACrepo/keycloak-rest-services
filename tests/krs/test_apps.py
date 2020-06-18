from krs.token import get_token
from krs import users,groups,apps

import pytest

from .util import keycloak_bootstrap

def test_list_apps_empty(keycloak_bootstrap):
    ret = apps.list_apps(token=keycloak_bootstrap)
    assert ret == {}

def test_list_apps(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)
    ret = apps.list_apps(token=keycloak_bootstrap)
    assert list(ret.keys()) == ['testapp']
    assert ret['testapp']['rootUrl'] == 'http://url'

def test_app_info(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)
    ret = apps.app_info('testapp', token=keycloak_bootstrap)
    assert ret['clientId'] == 'testapp'
    assert ret['rootUrl'] == 'http://url'
    assert 'clientSecret' in ret
    assert 'roles' in ret
    assert set(ret['roles']) == set(['read','write'])

def test_create_app(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)

def test_delete_app(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)
    apps.delete_app('testapp', token=keycloak_bootstrap)

def test_get_app_role_mappings_empty(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)
    ret = apps.get_app_role_mappings('testapp', token=keycloak_bootstrap)
    assert ret == {}

    with pytest.raises(Exception):
        apps.get_app_role_mappings('testapp', role='badrole', token=keycloak_bootstrap)

def test_add_app_role_mapping(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)

    with pytest.raises(Exception):
        apps.add_app_role_mapping('testapp', role='badrole', group='/badgroup', token=keycloak_bootstrap)

    with pytest.raises(Exception):
        apps.add_app_role_mapping('testapp', role='read', group='/badgroup', token=keycloak_bootstrap)

    groups.create_group('/testgroup', token=keycloak_bootstrap)
    apps.add_app_role_mapping('testapp', role='read', group='/testgroup', token=keycloak_bootstrap)

    ret = apps.get_app_role_mappings('testapp', token=keycloak_bootstrap)
    assert ret == {'read': ['/testgroup']}

def test_delete_app_role_mapping(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)
    groups.create_group('/testgroup', token=keycloak_bootstrap)
    apps.add_app_role_mapping('testapp', role='read', group='/testgroup', token=keycloak_bootstrap)

    with pytest.raises(Exception):
        apps.delete_app_role_mapping('testapp', role='badrole', group='/badgroup', token=keycloak_bootstrap)

    with pytest.raises(Exception):
        apps.delete_app_role_mapping('testapp', role='read', group='/badgroup', token=keycloak_bootstrap)

    apps.delete_app_role_mapping('testapp', role='read', group='/testgroup', token=keycloak_bootstrap)

    ret = apps.get_app_role_mappings('testapp', token=keycloak_bootstrap)
    assert ret == {}

def test_get_public_token(keycloak_bootstrap):
    apps.create_app('testapp', 'http://url', token=keycloak_bootstrap)
    groups.create_group('/testgroup', token=keycloak_bootstrap)
    apps.add_app_role_mapping('testapp', role='read', group='/testgroup', token=keycloak_bootstrap)

    users.create_user('testuser', 'test', 'user', 'test@user', token=keycloak_bootstrap)
    users.set_user_password('testuser', 'foo', token=keycloak_bootstrap)
    groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    ret = apps.get_public_token(username='testuser', password='foo', scopes=['testapp'], token=keycloak_bootstrap)
    assert ret['scope'] == 'testapp'
    assert ret['roles'] == {'testapp': ['read']}
