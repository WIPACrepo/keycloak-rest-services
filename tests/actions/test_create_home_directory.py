import asyncio
import pytest
import pytest_asyncio

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
from actions import create_home_directory

from ..util import keycloak_bootstrap, ldap_bootstrap


@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, tmp_path):
    attrs = {
        'homeDirectory': '/home/testuser',
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    await create_home_directory.process(tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'home/testuser'
    assert ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_homeDirectory(keycloak_bootstrap, tmp_path):
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    await create_home_directory.process(tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'home/testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_uidNumber(keycloak_bootstrap, tmp_path):
    attrs = {
        'homeDirectory': '/home/testuser',
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    await create_home_directory.process(tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'home/testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_gidNumber(keycloak_bootstrap, tmp_path):
    attrs = {
        'homeDirectory': '/home/testuser',
        'uidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    await create_home_directory.process(tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'home/testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_already_exists(keycloak_bootstrap, tmp_path):
    # if the path already exists, don't do anything, even if it's incorrect
    attrs = {
        'homeDirectory': '/home/testuser',
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    ret_path = tmp_path / 'home/testuser'
    (tmp_path / 'home').mkdir()
    ret_path.touch()

    await create_home_directory.process(tmp_path, keycloak_client=keycloak_bootstrap)

    assert ret_path.exists()
    assert not ret_path.is_dir()

@pytest_asyncio.fixture
async def listener(keycloak_bootstrap, tmp_path):
    rabbitmq.create_user('guest', 'guest')
    mq = create_home_directory.listener(root_dir=tmp_path, dedup=0, keycloak_client=keycloak_bootstrap)
    await mq.start()
    try:
        yield mq
    finally:
        await mq.stop()

@pytest.mark.asyncio
async def test_listener_create(keycloak_bootstrap, tmp_path, listener):
    attrs = {
        'homeDirectory': '/home/testuser',
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    ret_path = tmp_path / 'home/testuser'
    assert ret_path.is_dir()

@pytest.mark.asyncio
async def test_listener_other(keycloak_bootstrap, tmp_path, listener):
    attrs = {
        'homeDirectory': '/home/testuser',
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    await users.create_user('testuser2', first_name='first', last_name='last', email='foo@test2', rest_client=keycloak_bootstrap)

    ret_path = tmp_path / 'home/testuser2'
    assert not ret_path.is_dir()
