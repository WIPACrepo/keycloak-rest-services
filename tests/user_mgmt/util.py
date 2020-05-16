import time
import asyncio
import socket

import pytest
from rest_tools.server import Auth
from rest_tools.client import RestClient

from user_mgmt.server import create_server

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
async def rest(monkeypatch, port):
    monkeypatch.setenv('DEBUG', 'True')
    monkeypatch.setenv('PORT', str(port))
    monkeypatch.setenv('AUTH_SECRET', 'secret')
    monkeypatch.setenv('AUTH_ISSUER', 'issuer')
    monkeypatch.setenv('AUTH_ALGORITHM', 'HS512')

    s = create_server()
    def client(username='admin', groups=[], timeout=60):
        a = Auth('secret', issuer='issuer', algorithm='HS512')
        token = a.create_token(username, expiration=timeout, payload={
            'groups': groups,
        })
        print(token)
        return RestClient(f'http://localhost:{port}', token=token, timeout=timeout, retries=0)

    yield client
    s.stop()
    await asyncio.sleep(0.01)
