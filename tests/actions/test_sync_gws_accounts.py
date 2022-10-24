from unittest.mock import MagicMock

from actions.sync_gws_accounts import create_missing_eligible_accounts
from actions.sync_gws_accounts import activate_suspended_eligible_accounts
from actions.sync_gws_accounts import suspend_active_ineligible_accounts
from actions.sync_gws_accounts import get_gws_accounts


class MockHttpRequest:
    def execute(*args, **kwargs):
        pass


class MockGwsResource:
    def list(*args, **kwargs):
        return MockHttpRequest()

    def list_next(*args, **kwargs):
        return MockHttpRequest()

    def insert(*args, **kwargs):
        return MockHttpRequest()

    def update(*args, **kwargs):
        return MockHttpRequest()


KC_ACCOUNTS = {
    'add-to-gws': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True,},
    'already-in-gws': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True,},
    'ineligible': {'attributes': {'loginShell': '/sbin/nologin'}, 'enabled': True,},
    'suspend-1': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': False,},
    'suspend-2': {'enabled': True,},
    'activate': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True,},
}

GWS_ACCOUNTS = {
    'not-in-kc': {'primaryEmail': 'not-in-kc@i.w.e', 'suspended': False,},
    'already-in-gws': {'primaryEmail': 'already-in-gws@i.w.e', 'suspended': False,},
    'suspend-1': {'primaryEmail': 'suspend-1@i.w.e', 'suspended': False,},
    'suspend-2': {'primaryEmail': 'suspend-2@i.w.e', 'suspended': False,},
    'activate': {'primaryEmail': 'activate@i.w.e', 'suspended': True,},
}


def test_get_gws_accounts():
    request = MagicMock()
    request.execute = MagicMock(return_value={'users':[a for u,a in GWS_ACCOUNTS.items()]})
    gws_users_client = MagicMock()
    gws_users_client.list = MagicMock(return_value=request)
    gws_users_client.list_next = MagicMock(return_value=None)

    ret = get_gws_accounts(gws_users_client)

    gws_users_client.list.assert_called_once()
    gws_users_client.list_next.assert_called_once()
    request.execute.assert_called_once()
    assert ret == GWS_ACCOUNTS


def test_create_missing_eligible_accounts():
    ret = create_missing_eligible_accounts(MockGwsResource(), GWS_ACCOUNTS, KC_ACCOUNTS, dryrun=False)
    assert ret == ['add-to-gws']


def test_activate_suspended_eligible_accounts():
    ret = activate_suspended_eligible_accounts(MockGwsResource(), GWS_ACCOUNTS, KC_ACCOUNTS, dryrun=False)
    assert ret == ['activate']


def test_suspend_active_ineligible_accounts():
    ret = suspend_active_ineligible_accounts(MockGwsResource(), GWS_ACCOUNTS, KC_ACCOUNTS, dryrun=False)
    assert sorted(ret) == ['suspend-1', 'suspend-2']
