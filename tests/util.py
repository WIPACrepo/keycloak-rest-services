import os
from functools import partial

import pytest
from ldap3 import Connection
from rest_tools.client import RestClient
from wipac_dev_tools import from_environment
import requests

from krs import bootstrap
from krs.token import get_token
from krs import ldap
from krs import rabbitmq

@pytest.fixture
def keycloak_bootstrap(monkeypatch):
    monkeypatch.setenv('KEYCLOAK_REALM', 'testrealm')
    monkeypatch.setenv('KEYCLOAK_CLIENT_ID', 'testclient')
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')

    secret = bootstrap.bootstrap()
    monkeypatch.setenv('KEYCLOAK_CLIENT_SECRET', secret)

    # make sure rabbitmq is set up for tests
    tok = bootstrap.get_token()
    bootstrap.add_rabbitmq_listener(realm=os.environ['KEYCLOAK_REALM'], token=tok)

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
    monkeypatch.setenv('LDAP_GROUP_BASE', 'ou=groupTest,dc=icecube,dc=wisc,dc=edu')
    LDAP_GROUPS_BASE = 'ou=groupsTest,dc=icecube,dc=wisc,dc=edu'
    monkeypatch.setenv('LDAP_GROUPS_BASE', LDAP_GROUPS_BASE)

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
        ret = c.search(config["LDAP_GROUP_BASE"], '(cn=*)', attributes=['cn'])
        if ret:
            names = [e['cn'] for e in c.entries]
            for cn in names:
                c.delete(f'cn={cn},{config["LDAP_GROUP_BASE"]}')
        c.delete(config["LDAP_GROUP_BASE"])
        ret = c.search(LDAP_GROUPS_BASE, '(cn=*)', attributes=['cn'])
        if ret:
            names = [e['cn'] for e in c.entries]
            for cn in names:
                c.delete(f'cn={cn},{LDAP_GROUPS_BASE}')
        c.delete(LDAP_GROUPS_BASE)
    cleanup()

    args = {
        'ou': 'peopleTest',
    }
    c.add(config["LDAP_USER_BASE"], ['organizationalUnit', 'top'], args)
    args = {
        'ou': 'groupTest',
    }
    c.add(config["LDAP_GROUP_BASE"], ['organizationalUnit', 'top'], args)
    args = {
        'ou': 'groupsTest',
    }
    c.add(LDAP_GROUPS_BASE, ['organizationalUnit', 'top'], args)

    try:
        yield obj
    finally:
        cleanup()

@pytest.fixture(scope="session")
def rabbitmq_bootstrap():
    config = from_environment({
        'RABBITMQ_MGMT_URL': 'http://localhost:15672',
        'RABBITMQ_ADMIN_USER': 'admin',
        'RABBITMQ_ADMIN_PASSWORD': 'admin',
    })
    auth = (config['RABBITMQ_ADMIN_USER'], config['RABBITMQ_ADMIN_PASSWORD'])

    for _ in range(100):
        r = requests.get(f'{config["RABBITMQ_MGMT_URL"]}/api/users', auth=auth)
        try:
            r.raise_for_status()
        except Exception:
            time.sleep(1)
        else:
            break
    else:
        raise Exception('RabbitMQ is not responding!')

    rabbitmq.create_user('keycloak_guest', 'guest')
