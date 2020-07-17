import os
import time

import pytest
from rest_tools.client import OpenIDRestClient

from krs import bootstrap
from krs.token import get_token

@pytest.fixture
def keycloak_bootstrap(monkeypatch):
    monkeypatch.setenv('KEYCLOAK_REALM', 'testrealm')
    monkeypatch.setenv('KEYCLOAK_CLIENT_ID', 'testclient')
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')

    secret = bootstrap.bootstrap()
    monkeypatch.setenv('KEYCLOAK_CLIENT_SECRET', secret)

    token = get_token(os.environ['KEYCLOAK_URL'],
            client_id='testclient',
            client_secret=secret,
            refresh=True,
    )
    rest_client = OpenIDRestClient(
            f'{os.environ["KEYCLOAK_URL"]}/auth/admin/realms/testrealm',
            f'{os.environ["KEYCLOAK_URL"]}/auth/realms/master',
            refresh_token=token,
            client_id='testclient',
            client_secret=secret,
    )
    yield rest_client

    tok = bootstrap.get_token()
    bootstrap.delete_service_role('testclient', token=tok)
    bootstrap.delete_realm('testrealm', token=tok)
