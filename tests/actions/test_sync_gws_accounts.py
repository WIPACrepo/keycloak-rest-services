from unittest.mock import MagicMock

from actions.sync_gws_accounts import create_missing_eligible_accounts
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
    'add-to-gws': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True, 'firstName': 'Fn', 'lastName': 'Ln',},
    'already-in-gws': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True, 'firstName': 'Fn', 'lastName': 'Ln',},
    'ineligible-nologin': {'attributes': {'loginShell': '/sbin/nologin'}, 'enabled': True, 'firstName': 'Fn', 'lastName': 'Ln',},
    'no-shadow-expire': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True, 'firstName': 'Fn', 'lastName': 'Ln',},
    'expired-shadow': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True, 'firstName': 'Fn', 'lastName': 'Ln',},
    'missing-name': {'attributes': {'loginShell': '/bin/bash'}, 'enabled': True, 'firstName': '', 'lastName': 'Ln',},
}

GWS_ACCOUNTS = {
    'gws-only-account': {'primaryEmail': 'gws-only-account@i.w.e', 'suspended': False,},
    'already-in-gws': {'primaryEmail': 'already-in-gws@i.w.e', 'suspended': False,},  # noqa: F601
}

LDAP_ACCOUNTS = {
    'add-to-gws': {'shadowExpire': 99999},
    'already-in-gws': {'shadowExpire': 99999},  # noqa: F601
    'ineligible-nologin': {'shadowExpire': 99999},
    'no-shadow-expire': {},
    'expired-shadow': {'shadowExpire': 11111},
    'missing-name': {'shadowExpire': 99999},
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
    ret = create_missing_eligible_accounts(MockGwsResource(), GWS_ACCOUNTS, LDAP_ACCOUNTS,
                                           KC_ACCOUNTS, dryrun=False)
    assert ret == ['add-to-gws']
