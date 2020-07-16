import pytest

import krs.users
import krs.groups

from ..util import keycloak_bootstrap
from .util import port, server

def create_group_recursive(group_path, token):
    parts = group_path.strip('/').split('/')
    for i in range(1,len(parts)+1):
        krs.groups.create_group('/'+'/'.join(parts[:i]), token=token)

@pytest.mark.asyncio
async def test_experiments(server):
    rest, token = server
    client = rest('test')
    ret = await client.request('GET', '/api/experiments')
    assert ret == []

    create_group_recursive('/institutions/IceCube', token=token)

    ret = await client.request('GET', '/api/experiments')
    assert ret == ['IceCube']
