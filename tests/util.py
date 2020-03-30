import time

import pytest

from krs import bootstrap
from krs import token

@pytest.fixture
def keycloak_bootstrap(monkeypatch):
    monkeypatch.setenv('realm', 'testrealm')
    monkeypatch.setenv('client_id', 'testclient')

    secret = bootstrap.bootstrap()
    monkeypatch.setenv('client_secret', secret)

    yield token.get_token(from_cache=False)

    tok = bootstrap.get_token()
    bootstrap.delete_service_role('testclient', token=tok)
    bootstrap.delete_realm('testrealm', token=tok)
