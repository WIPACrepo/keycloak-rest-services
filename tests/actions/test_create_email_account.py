import pytest
import asyncio
import json
import subprocess

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
import actions.util
from actions import create_email_account

from ..util import keycloak_bootstrap, rabbitmq_bootstrap
from .util import patch_ssh_sudo, TestException


@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, patch_ssh_sudo):
    await users.create_user('testuser', first_name='First', last_name='Last', email='foo@test', attribs={'uidNumber':1000, 'gidNumber':1000}, rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'testuser', rest_client=keycloak_bootstrap)

    await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    user_dict = {'testuser': {'canonical': 'first.last', 'uid': 1000, 'gid': 1000}}
    assert json.loads(patch_ssh_sudo.call_args.args[1].split('\n')[6].split('=',1)[-1]) == user_dict

@pytest.mark.asyncio
async def test_create_error_ssh(keycloak_bootstrap, patch_ssh_sudo):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'testuser', rest_client=keycloak_bootstrap)

    patch_ssh_sudo.side_effect = TestException()

    with pytest.raises(TestException):
        await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_create_not_in_group(keycloak_bootstrap, patch_ssh_sudo):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)

    await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    user_dict = {}
    assert json.loads(patch_ssh_sudo.call_args.args[1].split('\n')[6].split('=',1)[-1]) == user_dict

@pytest.mark.asyncio
async def test_create_unicode(keycloak_bootstrap, patch_ssh_sudo):
    await users.create_user('foo', first_name='First', last_name='Mü Last', email='foo@test', attribs={'uidNumber':1000, 'gidNumber':1000}, rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'foo', rest_client=keycloak_bootstrap)

    await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    user_dict = {'foo': {'canonical': 'first.mulast', 'uid': 1000, 'gid': 1000}}
    assert json.loads(patch_ssh_sudo.call_args.args[1].split('\n')[6].split('=',1)[-1]) == user_dict


@pytest.fixture
@pytest.mark.asyncio
async def listener(keycloak_bootstrap, rabbitmq_bootstrap, tmp_path):
    mq = create_email_account.listener(email_server='test.test.test', group_path='/email', dedup=None, keycloak_client=keycloak_bootstrap)
    await mq.start()
    try:
        yield mq
    finally:
        await mq.stop()

@pytest.mark.asyncio
async def test_listener_create(keycloak_bootstrap, tmp_path, listener, patch_ssh_sudo):
    await users.create_user('testuser', first_name='First', last_name='Last', email='foo@test', attribs={'uidNumber':1000, 'gidNumber':1000}, rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'testuser', rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    patch_ssh_sudo.assert_called_once()
    assert patch_ssh_sudo.call_args.args[0] == 'test.test.test'

    user_dict = {'testuser': {'canonical': 'first.last', 'uid': 1000, 'gid': 1000}}
    assert json.loads(patch_ssh_sudo.call_args.args[1].split('\n')[6].split('=',1)[-1]) == user_dict
