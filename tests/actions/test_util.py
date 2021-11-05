import pytest
from actions.util import ssh, scp_and_run, scp_and_run_sudo

from .util import TestException


def test_ssh(mocker):
    cc = mocker.patch('subprocess.check_call')

    ssh('test.test.test', 'arg1', 'arg2')

    cc.assert_called_once()
    assert 'test.test.test' in cc.call_args.args[0]
    assert cc.call_args.args[0][-2:] == ['arg1', 'arg2']

def test_scp_and_run(mocker):
    cc = mocker.patch('subprocess.check_call')

    scp_and_run('test.test.test', 'data data data')

    assert cc.call_count == 3
    assert cc.call_args_list[0].args[0][0] == 'scp'
    assert cc.call_args_list[1].args[0][0] == 'ssh'
    assert cc.call_args_list[2].args[0][0] == 'ssh'

def test_scp_and_run_error(mocker):
    cc = mocker.patch('subprocess.check_call')
    cc.side_effect = TestException()

    with pytest.raises(TestException):
        scp_and_run('test.test.test', 'data data data')

def test_scp_and_run_sudo(mocker):
    cc = mocker.patch('subprocess.check_call')

    scp_and_run_sudo('test.test.test', 'data data data')

    assert cc.call_count == 3
    assert cc.call_args_list[0].args[0][0] == 'scp'
    assert cc.call_args_list[1].args[0][0] == 'ssh'
    assert 'sudo' in cc.call_args_list[1].args[0]
    assert cc.call_args_list[2].args[0][0] == 'ssh'

def test_scp_and_run_sudo_error(mocker):
    cc = mocker.patch('subprocess.check_call')
    cc.side_effect = TestException()

    with pytest.raises(TestException):
        scp_and_run_sudo('test.test.test', 'data data data')
