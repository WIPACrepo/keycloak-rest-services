import asyncio
import pytest
import pytest_asyncio

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
from actions import create_user_directory

from ..util import keycloak_bootstrap, rabbitmq_bootstrap


@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, tmp_path):
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_user_directory.process('/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'testuser'
    assert ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_uidNumber(keycloak_bootstrap, tmp_path):
    attrs = {
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_user_directory.process('/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_gidNumber(keycloak_bootstrap, tmp_path):
    attrs = {
        'uidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_user_directory.process('/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_group(keycloak_bootstrap, tmp_path):
    attrs = {
        'gidNumber': 12345,
        'uidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)

    await create_user_directory.process('/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    ret_path = tmp_path / 'testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_already_exists(keycloak_bootstrap, tmp_path):
    # if the path already exists, don't do anything, even if it's incorrect
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    ret_path = tmp_path / 'testuser'
    ret_path.touch()

    await create_user_directory.process('/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    assert ret_path.exists()
    assert not ret_path.is_dir()

@pytest_asyncio.fixture
async def listener(keycloak_bootstrap, rabbitmq_bootstrap, tmp_path):
    mq = create_user_directory.listener(group_path='/posix', root_dir=tmp_path, dedup=None, keycloak_client=keycloak_bootstrap)
    await mq.start()
    try:
        yield mq
    finally:
        await mq.stop()

@pytest.mark.asyncio
async def test_listener_create(keycloak_bootstrap, tmp_path, listener):
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    ret_path = tmp_path / 'testuser'
    assert ret_path.is_dir()

@pytest.mark.asyncio
async def test_listener_other(keycloak_bootstrap, tmp_path, listener):
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    ret_path = tmp_path / 'testuser'
    assert ret_path.is_dir()

    await users.create_user('testuser2', first_name='first', last_name='last', email='foo@test2', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser2', rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    ret_path = tmp_path / 'testuser2'
    assert not ret_path.is_dir()
