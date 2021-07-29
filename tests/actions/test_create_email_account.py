import pytest
import asyncio
import json
import subprocess

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
from actions import create_email_account

from ..util import keycloak_bootstrap, rabbitmq_bootstrap


class TestException(Exception):
    pass

@pytest.fixture
def patch_ssh(mocker):
    return mocker.patch('actions.create_email_account.scp_and_run')

def test_ssh(mocker):
    cc = mocker.patch('subprocess.check_call')

    create_email_account.ssh('test.test.test', 'arg1', 'arg2')

    cc.assert_called_once()
    assert 'test.test.test' in cc.call_args.args[0]
    assert cc.call_args.args[0][-2:] == ['arg1', 'arg2']

def test_scp_and_run(mocker):
    cc = mocker.patch('subprocess.check_call')

    create_email_account.scp_and_run('test.test.test', 'data data data')

    assert cc.call_count == 3
    assert cc.call_args_list[0].args[0][0] == 'scp'
    assert cc.call_args_list[1].args[0][0] == 'ssh'
    assert cc.call_args_list[2].args[0][0] == 'ssh'

def test_scp_and_run_error(mocker):
    cc = mocker.patch('subprocess.check_call')
    cc.side_effect = TestException()

    with pytest.raises(TestException):
        create_email_account.scp_and_run('test.test.test', 'data data data')

@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, patch_ssh):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'testuser', rest_client=keycloak_bootstrap)

    await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

    patch_ssh.assert_called_once()
    assert patch_ssh.call_args.args[0] == 'test.test.test'

    user_dict = {'testuser': {'firstName': 'first', 'lastName': 'last'}}
    assert json.loads(patch_ssh.call_args.args[1].split('\n')[1].split('=',1)[-1]) == user_dict

@pytest.mark.asyncio
async def test_create_error_ssh(keycloak_bootstrap, patch_ssh):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'testuser', rest_client=keycloak_bootstrap)

    patch_ssh.side_effect = TestException()

    with pytest.raises(TestException):
        await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_create_not_in_group(keycloak_bootstrap, patch_ssh):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)

    await create_email_account.process('test.test.test', '/email', keycloak_client=keycloak_bootstrap)

    patch_ssh.assert_called_once()
    assert patch_ssh.call_args.args[0] == 'test.test.test'

    user_dict = {}
    assert json.loads(patch_ssh.call_args.args[1].split('\n')[1].split('=',1)[-1]) == user_dict


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
async def test_listener_create(keycloak_bootstrap, tmp_path, listener, patch_ssh):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/email', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/email', 'testuser', rest_client=keycloak_bootstrap)

    await asyncio.sleep(.25) # allow listener to run

    patch_ssh.assert_called_once()
    assert patch_ssh.call_args.args[0] == 'test.test.test'

    user_dict = {'testuser': {'firstName': 'first', 'lastName': 'last'}}
    assert json.loads(patch_ssh.call_args.args[1].split('\n')[1].split('=',1)[-1]) == user_dict
