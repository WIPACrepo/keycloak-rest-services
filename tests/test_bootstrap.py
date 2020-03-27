from krs import bootstrap

def test_wait_for_keycloak(monkeypatch):
    bootstrap.wait_for_keycloak()

def test_token(monkeypatch):
    bootstrap.wait_for_keycloak()
    bootstrap.get_token()
