import os

import pytest

from krs.token import get_token
from krs import users,groups,apps

from ..util import keycloak_bootstrap

@pytest.mark.asyncio
async def test_list_apps_empty(keycloak_bootstrap):
    ret = await apps.list_apps(rest_client=keycloak_bootstrap)
    assert ret == {}

@pytest.mark.asyncio
async def test_list_apps(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)
    ret = await apps.list_apps(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['testapp']
    assert ret['testapp']['rootUrl'] == 'http://url'

@pytest.mark.asyncio
async def test_app_info(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)
    ret = await apps.app_info('testapp', rest_client=keycloak_bootstrap)
    assert ret['clientId'] == 'testapp'
    assert ret['rootUrl'] == 'http://url'
    assert 'clientSecret' in ret
    assert 'roles' in ret
    assert set(ret['roles']) == set(['read','write'])

@pytest.mark.asyncio
async def test_create_app(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_delete_app(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)
    await apps.delete_app('testapp', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_get_app_role_mappings_empty(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)
    ret = await apps.get_app_role_mappings('testapp', rest_client=keycloak_bootstrap)
    assert ret == {}

    with pytest.raises(Exception):
        await apps.get_app_role_mappings('testapp', role='badrole', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_add_app_role_mapping(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)

    with pytest.raises(Exception):
        await apps.add_app_role_mapping('testapp', role='badrole', group='/badgroup', rest_client=keycloak_bootstrap)

    with pytest.raises(Exception):
        await apps.add_app_role_mapping('testapp', role='read', group='/badgroup', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await apps.add_app_role_mapping('testapp', role='read', group='/testgroup', rest_client=keycloak_bootstrap)

    ret = await apps.get_app_role_mappings('testapp', rest_client=keycloak_bootstrap)
    assert ret == {'read': ['/testgroup']}

@pytest.mark.asyncio
async def test_delete_app_role_mapping(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await apps.add_app_role_mapping('testapp', role='read', group='/testgroup', rest_client=keycloak_bootstrap)

    with pytest.raises(Exception):
        await apps.delete_app_role_mapping('testapp', role='badrole', group='/badgroup', rest_client=keycloak_bootstrap)

    with pytest.raises(Exception):
        await apps.delete_app_role_mapping('testapp', role='read', group='/badgroup', rest_client=keycloak_bootstrap)

    await apps.delete_app_role_mapping('testapp', role='read', group='/testgroup', rest_client=keycloak_bootstrap)

    ret = await apps.get_app_role_mappings('testapp', rest_client=keycloak_bootstrap)
    assert ret == {}

@pytest.mark.asyncio
async def test_get_public_token(keycloak_bootstrap):
    await apps.create_app('testapp', 'http://url', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await apps.add_app_role_mapping('testapp', role='read', group='/testgroup', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', 'test', 'user', 'test@user', rest_client=keycloak_bootstrap)
    await users.set_user_password('testuser', 'foo', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    url = f'{os.environ["KEYCLOAK_URL"]}/auth/realms/{os.environ["KEYCLOAK_REALM"]}'
    ret = apps.get_public_token(username='testuser', password='foo', scopes=['testapp'], openid_url=url)
    assert ret['scope'] == 'testapp'
    assert ret['roles'] == {'testapp': ['read']}
