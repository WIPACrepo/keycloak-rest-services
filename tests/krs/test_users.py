import pytest

from krs.token import get_token
from krs import users

from ..util import keycloak_bootstrap

@pytest.mark.asyncio
async def test_list_users_empty(keycloak_bootstrap):
    ret = await users.list_users(rest_client=keycloak_bootstrap)
    assert ret == {}

@pytest.mark.asyncio
async def test_list_users(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    ret = await users.list_users(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['testuser']
    assert ret['testuser']['firstName'] == 'first'
    assert ret['testuser']['lastName'] == 'last'
    assert ret['testuser']['email'] == 'foo@test'

@pytest.mark.asyncio
async def test_user_info(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['firstName'] == 'first'
    assert ret['lastName'] == 'last'
    assert ret['email'] == 'foo@test'

@pytest.mark.asyncio
async def test_create_user(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_modify_user(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', {'foo': 'bar'}, rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'foo' in ret['attributes']
    assert ret['attributes']['foo'] == 'bar'

@pytest.mark.asyncio
async def test_set_user_password(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.set_user_password('testuser', 'foo', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_set_user_password_bad(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    with pytest.raises(Exception):
        await users.set_user_password('testuser', ['f', 'o', 'o'], rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_delete_user(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.delete_user('testuser', rest_client=keycloak_bootstrap)
