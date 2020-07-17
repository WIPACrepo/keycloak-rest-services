import time
import asyncio
import socket
import os

import pytest
from rest_tools.server import Auth, from_environment
from rest_tools.client import RestClient
import motor.motor_asyncio

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
    monkeypatch.setenv('AUTH_OPENID_URL', f'{os.environ["KEYCLOAK_URL"]}/auth/realms/{os.environ["KEYCLOAK_REALM"]}/')

    krs.bootstrap.user_mgmt_app(f'http://localhost:{port}', passwordGrant=True, token=krs.bootstrap.get_token())

    s = create_server()
    async def client(username='admin', groups=[], timeout=10):
        await krs.users.create_user(username, 'first', 'last', username+'@test', rest_client=keycloak_bootstrap)
        await krs.users.set_user_password(username, 'test', rest_client=keycloak_bootstrap)
        for group in groups:
            await krs.groups.create_group(group, rest_client=keycloak_bootstrap)
            await krs.groups.add_user_group(group, username, rest_client=keycloak_bootstrap)

        token = krs.apps.get_public_token(username=username, password='test',
                                          scopes=['profile'], client='user_mgmt',
                                          openid_url=os.environ["AUTH_OPENID_URL"],
                                          raw=True)
        print(token)

        return RestClient(f'http://localhost:{port}', token=token, timeout=timeout, retries=0)

    yield client, keycloak_bootstrap, f'http://localhost:{port}'
    await s.stop()

@pytest.fixture
async def mongo_client():
    default_config = {
       'DB_URL': 'mongodb://localhost/keycloak_user_mgmt',
    }
    config = from_environment(default_config)
    db = motor.motor_asyncio.AsyncIOMotorClient(config['DB_URL'])
    db_name = config['DB_URL'].split('/')[-1]
    ret = db[db_name]

    await ret.user_registrations.drop()
    await ret.inst_approvals.drop()
    await ret.group_approvals.drop()
    try:
        yield ret
    finally:
        await ret.user_registrations.drop()
        await ret.inst_approvals.drop()
        await ret.group_approvals.drop()
