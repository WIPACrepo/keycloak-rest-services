from krs import bootstrap

def test_wait_for_keycloak(monkeypatch):
    bootstrap.wait_for_keycloak()

def test_token(monkeypatch):
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')
    bootstrap.wait_for_keycloak()
    bootstrap.get_token()

def test_realm(monkeypatch):
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')
    bootstrap.wait_for_keycloak()
    tok = bootstrap.get_token()
    bootstrap.create_realm('testrealm', token=tok)

    # cleanup
    bootstrap.delete_realm('testrealm', token=tok)

def test_create_public_app(monkeypatch):
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')
    bootstrap.wait_for_keycloak()
    tok = bootstrap.get_token()
    bootstrap.create_realm('testrealm', token=tok)
    bootstrap.create_public_app(realm='testrealm', token=tok)

    # cleanup
    bootstrap.delete_realm('testrealm', token=tok)

def test_create_service_role(monkeypatch):
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')
    bootstrap.wait_for_keycloak()
    tok = bootstrap.get_token()
    bootstrap.create_realm('testrealm', token=tok)
    bootstrap.create_service_role('testclient', realm='testrealm', token=tok)

    # cleanup
    bootstrap.delete_service_role('testclient', token=tok)
    bootstrap.delete_realm('testrealm', token=tok)

def test_bootstrap(monkeypatch):
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')
    monkeypatch.setenv('KEYCLOAK_REALM', 'testrealm')
    monkeypatch.setenv('KEYCLOAK_CLIENT_ID', 'testclient')
    bootstrap.bootstrap()

    # cleanup
    tok = bootstrap.get_token()
    bootstrap.delete_service_role('testclient', token=tok)
    bootstrap.delete_realm('testrealm', token=tok)

def test_bootstrap_user_mgmt(monkeypatch):
    monkeypatch.setenv('USERNAME', 'admin')
    monkeypatch.setenv('PASSWORD', 'admin')
    monkeypatch.setenv('KEYCLOAK_REALM', 'testrealm')
    monkeypatch.setenv('KEYCLOAK_CLIENT_ID', 'testclient')
    bootstrap.wait_for_keycloak()
    tok = bootstrap.get_token()
    bootstrap.create_realm('testrealm', token=tok)
    bootstrap.user_mgmt_app(f'http://localhost:9999', passwordGrant=True, token=tok)