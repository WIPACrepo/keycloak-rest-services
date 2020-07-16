import pytest

import krs.users
import krs.groups

from ..util import keycloak_bootstrap
from .util import port, server

async def create_group_recursive(group_path, token):
    parts = group_path.strip('/').split('/')
    for i in range(1,len(parts)+1):
        await krs.groups.create_group('/'+'/'.join(parts[:i]), token=token)

@pytest.mark.asyncio
async def test_experiments(server):
    rest, token = server
    client = await rest('test')
    ret = await client.request('GET', '/api/experiments')
    assert ret == []

    await create_group_recursive('/institutions/IceCube', token=token)

    ret = await client.request('GET', '/api/experiments')
    assert ret == ['IceCube']

@pytest.mark.asyncio
async def test_institutions(server):
    rest, token = server
    client = await rest('test')

    await create_group_recursive('/institutions/IceCube', token=token)
    
    ret = await client.request('GET', '/api/experiments/IceCube/institutions')
    assert ret == []

    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    ret = await client.request('GET', '/api/experiments/IceCube/institutions')
    assert ret == ['UW-Madison']
