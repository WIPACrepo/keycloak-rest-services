import time
import asyncio
import socket

import pytest
from rest_tools.server import Auth
from rest_tools.client import RestClient

from user_mgmt.server import create_server

import krs.bootstrap
import krs.users
import krs.groups
import krs.apps

from ..util import keycloak_bootstrap

@pytest.fixture
def port():
    """Get an ephemeral port number."""
    # https://unix.stackexchange.com/a/132524
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    addr = s.getsockname()
    ephemeral_port = addr[1]
    s.close()
    return ephemeral_port

@pytest.fixture
async def server(monkeypatch, port, keycloak_bootstrap):
    monkeypatch.setenv('DEBUG', 'True')
    monkeypatch.setenv('PORT', str(port))
    monkeypatch.setenv('AUTH_SECRET', 'secret')
    monkeypatch.setenv('AUTH_ISSUER', 'issuer')
    monkeypatch.setenv('AUTH_ALGORITHM', 'HS512')

    krs.bootstrap.user_mgmt_app(f'http://localhost:{port}', passwordGrant=True, token=keycloak_bootstrap)

    s = create_server()
    async def client(username='admin', groups=[], timeout=60):
        await krs.users.create_user(username, 'first', 'last', 'email@test', token=keycloak_bootstrap)
        await krs.users.set_user_password(username, 'test', token=keycloak_bootstrap)
        for group in groups:
            await krs.groups.create_group(group, token=keycloak_bootstrap)
            await krs.groups.add_user_group(group, username, token=keycloak_bootstrap)

        token = krs.apps.get_public_token(username=username, password='test',
                                          scopes=['profile'], client='user_mgmt',
                                          raw=True)
        print(token)

        return RestClient(f'http://localhost:{port}', token=token, timeout=timeout, retries=0)

    yield client, keycloak_bootstrap
    s.stop()
    await asyncio.sleep(0.01)
