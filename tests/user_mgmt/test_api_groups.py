import asyncio

import pytest
from rest_tools.client import AsyncSession

import krs.users
import krs.groups

from ..util import keycloak_bootstrap
from .util import port, server, mongo_client



@pytest.mark.asyncio
async def test_groups(server):
    rest, token, *_ = server
    client = await rest('test')

    await krs.groups.create_group('/foo', token=token)
    
    ret = await client.request('GET', '/api/groups')
    assert ret == {} # /foo is not self-administrered yet

    await krs.groups.create_group('/foo/_admin', token=token)
    
    ret = await client.request('GET', '/api/groups')
    assert list(ret.keys()) == ['/foo']

@pytest.mark.asyncio
async def test_group_members(server):
    rest, token, *_ = server
    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)

    group_id = (await krs.groups.group_info('/foo', token=token))['id']

    client = await rest('test')
    client2 = await rest('test2', ['/foo/_admin'])

    with pytest.raises(Exception):
        ret = await client.request('GET', f'/api/groups/{group_id}')

    ret = await client2.request('GET', f'/api/groups/{group_id}')
    assert ret == [] # no members

    await krs.groups.add_user_group('/foo', 'test', token=token)

    ret = await client2.request('GET', f'/api/groups/{group_id}')
    assert ret == ['test']

@pytest.mark.asyncio
async def test_group_members_add(server):
    rest, token, *_ = server
    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)

    group_id = (await krs.groups.group_info('/foo', token=token))['id']

    client = await rest('test')
    client2 = await rest('test2', ['/foo/_admin'])

    with pytest.raises(Exception):
        ret = await client.request('PUT', f'/api/groups/{group_id}/test')

    await client2.request('PUT', f'/api/groups/{group_id}/test')
    ret = await krs.groups.get_group_membership('/foo', token=token)
    assert ret == ['test']

@pytest.mark.asyncio
async def test_group_members_delete(server):
    rest, token, *_ = server
    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)

    group_id = (await krs.groups.group_info('/foo', token=token))['id']

    client = await rest('test', ['/foo'])
    client2 = await rest('test2', ['/foo/_admin'])

    with pytest.raises(Exception):
        ret = await client.request('DELETE', f'/api/groups/{group_id}/test')

    await client2.request('DELETE', f'/api/groups/{group_id}/test')
    ret = await krs.groups.get_group_membership('/foo', token=token)
    assert ret == []

@pytest.mark.asyncio
async def test_group_approvals(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)
    await krs.groups.create_group('/bar', token=token)

    client = await rest('test')

    # missing group key
    with pytest.raises(Exception):
        await client.request('POST', '/api/group_approvals')

    # try to join a non-self-administered group
    data = {
        'group': '/bar',
    }
    with pytest.raises(Exception):
        await client.request('POST', '/api/group_approvals', data)

    # try to join a proper self-administered group
    data = {
        'group': '/foo',
    }
    ret = await client.request('POST', '/api/group_approvals', data)
    approval_id = ret['id']

    ret = await mongo_client.group_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id
    assert ret[0]['group'] == data['group']

@pytest.mark.asyncio
async def test_group_approvals_get(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)

    client = await rest('test')
    client2 = await rest('test2', groups=['/foo/_admin'])

    data = {
        'group': '/foo',
    }
    ret = await client.request('POST', '/api/group_approvals', data)
    approval_id = ret['id']

    # no auth
    ret = await client.request('GET', '/api/group_approvals')
    assert ret == []

    # success
    ret = await client2.request('GET', '/api/group_approvals')

    assert len(ret) == 1
    assert ret[0]['id'] == approval_id
    assert ret[0]['group'] == data['group']
    assert ret[0]['username'] == 'test'

@pytest.mark.asyncio
async def test_group_approvals_actions_approve(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)

    client = await rest('test')
    client2 = await rest('test2', groups=['/foo/_admin'])

    data = {
        'group': '/foo',
    }
    ret = await client.request('POST', '/api/group_approvals', data)
    approval_id = ret['id']

    # no auth
    with pytest.raises(Exception):
        await client.request('POST', f'/api/group_approvals/{approval_id}/actions/approve')

    ret = await mongo_client.group_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id

    ret = await krs.groups.get_group_membership('/foo', token=token)
    assert 'test' not in ret

    # success
    await client2.request('POST', f'/api/group_approvals/{approval_id}/actions/approve')

    ret = await mongo_client.group_approvals.find().to_list(10)
    assert len(ret) == 0

    ret = await krs.groups.get_group_membership('/foo', token=token)
    assert 'test' in ret

@pytest.mark.asyncio
async def test_group_approvals_actions_deny(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/foo', token=token)
    await krs.groups.create_group('/foo/_admin', token=token)

    client = await rest('test')
    client2 = await rest('test2', groups=['/foo/_admin'])

    data = {
        'group': '/foo',
    }
    ret = await client.request('POST', '/api/group_approvals', data)
    approval_id = ret['id']

    # no auth
    with pytest.raises(Exception):
        await client.request('POST', f'/api/group_approvals/{approval_id}/actions/deny')

    ret = await mongo_client.group_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id

    ret = await krs.groups.get_group_membership('/foo', token=token)
    assert 'test' not in ret

    # success
    await client2.request('POST', f'/api/group_approvals/{approval_id}/actions/deny')

    ret = await mongo_client.group_approvals.find().to_list(10)
    assert len(ret) == 0

    ret = await krs.groups.get_group_membership('/foo', token=token)
    assert 'test' not in ret

