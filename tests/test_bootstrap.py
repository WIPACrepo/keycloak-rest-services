from krs import bootstrap

def test_wait_for_keycloak(monkeypatch):
    bootstrap.wait_for_keycloak()

def test_token(monkeypatch):
    bootstrap.wait_for_keycloak()
    bootstrap.get_token()

def test_realm(monkeypatch):
    bootstrap.wait_for_keycloak()
    tok = bootstrap.get_token()
    bootstrap.create_realm('testrealm', token=tok)
    bootstrap.delete_realm('testrealm', token=tok)

def test_create_service_role(monkeypatch):
    bootstrap.wait_for_keycloak()
    tok = bootstrap.get_token()
    bootstrap.create_realm('testrealm', token=tok)
    bootstrap.create_service_role('testclient', realm='testrealm', token=tok)

def test_bootstrap(monkeypatch):
    monkeypatch.setenv('realm', 'testrealm')
    monkeypatch.setenv('client_id', 'testclient')
    bootstrap.bootstrap()
