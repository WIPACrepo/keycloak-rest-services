import pytest

from .util import port, rest

@pytest.mark.asyncio
async def test_users(rest):
    client = rest()
    ret = await client.request('GET', '/api/users')

@pytest.mark.asyncio
async def test_individual_user(rest):
    client = rest()
    ret = await client.request('GET', '/api/users/foo')

@pytest.mark.asyncio
async def test_user_groups(rest):
    client = rest()
    ret = await client.request('GET', '/api/users/foo/groups')
    assert 'groups' in ret
