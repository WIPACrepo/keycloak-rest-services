import os
from functools import partial

import pytest
from ldap3 import Connection
from rest_tools.client import RestClient

from krs import bootstrap
from krs.token import get_token
from krs import ldap

@pytest.fixture
def keycloak_bootstrap(monkeypatch):
    monkeypatch.setenv('KEYCLOAK_REALM', 'testrealm')
    monkeypatch.setenv('KEYCLOAK_CLIENT_ID', 'testclient')
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')

    secret = bootstrap.bootstrap()
    monkeypatch.setenv('KEYCLOAK_CLIENT_SECRET', secret)

    token = partial(get_token, os.environ['KEYCLOAK_URL'],
            client_id='testclient',
            client_secret=secret,
    )
    rest_client = RestClient(
        f'{os.environ["KEYCLOAK_URL"]}/auth/admin/realms/testrealm',
        token=token,
        retries=0,
    )
    yield rest_client

    tok = bootstrap.get_token()
    bootstrap.delete_service_role('testclient', token=tok)
    bootstrap.delete_realm('testrealm', token=tok)


@pytest.fixture
def ldap_bootstrap(monkeypatch):
    monkeypatch.setenv('LDAP_USER_BASE', 'ou=peopleTest,dc=icecube,dc=wisc,dc=edu')

    obj = ldap.LDAP()
    config = obj.config

    c = Connection(config['LDAP_URL'], user=config['LDAP_ADMIN_USER'], password=config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

    def cleanup():
        ret = c.search(config["LDAP_USER_BASE"], '(uid=*)', attributes=['uid'])
        if ret:
            uids = [e['uid'] for e in c.entries]
            for uid in uids:
                c.delete(f'uid={uid},{config["LDAP_USER_BASE"]}')
        c.delete(config["LDAP_USER_BASE"])
    cleanup()

    args = {
        'ou': 'peopleTest',
    }
    c.add(config["LDAP_USER_BASE"], ['organizationalUnit', 'top'], args)

    try:
        yield obj
    finally:
        cleanup()
