import asyncio
import pytest
import pytest_asyncio

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
from actions import create_user_directory_ssh

from ..util import keycloak_bootstrap, rabbitmq_bootstrap
from .util import patch_ssh_sudo, TestException

@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, tmp_path, patch_ssh_sudo):
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_user_directory_ssh.process('test.test.test', '/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    exec(patch_ssh_sudo.call_args.args[1])

    ret_path = tmp_path / 'testuser'
    assert ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_uidNumber(keycloak_bootstrap, tmp_path, patch_ssh_sudo):
    attrs = {
        'gidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_user_directory_ssh.process('test.test.test', '/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    exec(patch_ssh_sudo.call_args.args[1])

    ret_path = tmp_path / 'testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_gidNumber(keycloak_bootstrap, tmp_path, patch_ssh_sudo):
    attrs = {
        'uidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_user_directory_ssh.process('test.test.test', '/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    exec(patch_ssh_sudo.call_args.args[1])

    ret_path = tmp_path / 'testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_missing_group(keycloak_bootstrap, tmp_path, patch_ssh_sudo):
    attrs = {
        'gidNumber': 12345,
        'uidNumber': 12345,
    }
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)

    await create_user_directory_ssh.process('test.test.test', '/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    exec(patch_ssh_sudo.call_args.args[1])

    ret_path = tmp_path / 'testuser'
    assert not ret_path.is_dir()

@pytest.mark.asyncio
async def test_already_exists(keycloak_bootstrap, tmp_path, patch_ssh_sudo):
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

    await create_user_directory_ssh.process('test.test.test', '/posix', tmp_path, keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    exec(patch_ssh_sudo.call_args.args[1])

    assert ret_path.exists()
    assert not ret_path.is_dir()

@pytest_asyncio.fixture
async def listener(keycloak_bootstrap, rabbitmq_bootstrap, tmp_path):
    mq = create_user_directory_ssh.listener(server='test.test.test',
            group_path='/posix', root_dir=tmp_path, dedup=None, keycloak_client=keycloak_bootstrap)
    await mq.start()
    try:
        yield mq
    finally:
        await mq.stop()

@pytest.mark.asyncio
async def test_listener_create(keycloak_bootstrap, tmp_path, listener, patch_ssh_sudo):
    attrs = {
        'uidNumber': 12345,
        'gidNumber': 12345,
    }
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs=attrs, rest_client=keycloak_bootstrap) # triggers dir creation
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    exec(patch_ssh_sudo.call_args.args[1])

    ret_path = tmp_path / 'testuser'
    assert ret_path.is_dir()
