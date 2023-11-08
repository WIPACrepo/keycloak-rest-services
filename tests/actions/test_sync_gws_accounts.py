from unittest.mock import MagicMock

from actions.sync_gws_accounts import create_missing_eligible_accounts
from actions.sync_gws_accounts import get_gws_accounts


KC_ACCOUNTS = {
    'add-to-gws': {'attributes': {'loginShell': '/bin/bash'},
                   'username': 'add-to-gws', 'enabled': True, 'firstName': 'Fn',
                   'lastName': 'Ln'},
    'add-to-gws-w-alias': {'attributes': {'loginShell': '/bin/bash',
                                          'canonical_email': 'foo@bar.com'},
                           'username': 'add-to-gws-w-alias', 'enabled': True,
                           'firstName': 'Fn', 'lastName': 'Ln', },
    'force-creation': {'attributes': {'loginShell': '/sbin/nologin',
                                      'force_creation_in_gws': 'true'},
                       'username': 'force-creation', 'enabled': True, 'firstName': 'Fn',
                       'lastName': 'Ln'},
    'force-creation-invalid': {'attributes': {'loginShell': '/sbin/nologin',
                                              'force_creation_in_gws': 'TRUE'},
                               'username': 'force-creation-invalid', 'enabled': True,
                               'firstName': 'Fn', 'lastName': 'Ln'},
    'already-in-gws': {'attributes': {'loginShell': '/bin/bash'},
                       'username': 'already-in-gws', 'enabled': True, 'firstName': 'Fn',
                       'lastName': 'Ln'},
    'ineligible-nologin': {'attributes': {'loginShell': '/sbin/nologin'},
                           'username': 'ineligible-nologin', 'enabled': True,
                           'firstName': 'Fn', 'lastName': 'Ln'},
    'no-shadow-expire': {'attributes': {'loginShell': '/bin/bash'},
                         'username': 'no-shadow-expire', 'enabled': True,
                         'firstName': 'Fn', 'lastName': 'Ln'},
    'expired-shadow': {'attributes': {'loginShell': '/bin/bash'},
                       'username': 'expired-shadow', 'enabled': True,
                       'firstName': 'Fn', 'lastName': 'Ln'},
    'missing-name': {'attributes': {'loginShell': '/bin/bash'},
                     'username': 'missing-name', 'enabled': True, 'firstName': '',
                     'lastName': 'Ln'},
}

GWS_ACCOUNTS = {
    'gws-only-account': {'primaryEmail': 'gws-only-account@i.w.e', 'suspended': False},
    'already-in-gws': {'primaryEmail': 'already-in-gws@i.w.e', 'suspended': False},  # noqa: F601
}

LDAP_ACCOUNTS = {
    'add-to-gws': {'shadowExpire': 99999},
    'add-to-gws-w-alias': {'shadowExpire': 99999},
    'force-creation': {'shadowExpire': 11111},
    'force-creation-invalid': {'shadowExpire': 11111},
    'already-in-gws': {'shadowExpire': 99999},  # noqa: F601
    'ineligible-nologin': {'shadowExpire': 99999},
    'no-shadow-expire': {},
    'expired-shadow': {'shadowExpire': 11111},
    'missing-name': {'shadowExpire': 99999},
}


def test_get_gws_accounts():
    request = MagicMock()
    request.execute = MagicMock(return_value={'users': [a for u, a in GWS_ACCOUNTS.items()]})
    gws_users_client = MagicMock()
    gws_users_client.list = MagicMock(return_value=request)
    gws_users_client.list_next = MagicMock(return_value=None)

    ret = get_gws_accounts(gws_users_client)

    gws_users_client.list.assert_called_once()
    gws_users_client.list_next.assert_called_once()
    request.execute.assert_called_once()
    assert ret == GWS_ACCOUNTS


def test_create_missing_eligible_accounts():
    gws_users_client = MagicMock()
    gws_creds = None

    ret = create_missing_eligible_accounts(gws_users_client, GWS_ACCOUNTS, LDAP_ACCOUNTS,
                                           KC_ACCOUNTS, gws_creds, dryrun=False)

    assert sorted(ret) == sorted(['add-to-gws', 'add-to-gws-w-alias', 'force-creation'])

    assert gws_users_client.insert().execute.call_count == 3
    assert gws_users_client.aliases.call_count == 1
    assert gws_users_client.aliases().insert().execute.call_count == 1
