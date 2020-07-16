import asyncio

import pytest
from rest_tools.client import AsyncSession

import krs.users
import krs.groups

from ..util import keycloak_bootstrap
from .util import port, server, mongo_client


@pytest.mark.asyncio
async def test_experiments(server):
    rest, token, *_ = server
    client = await rest('test')
    ret = await client.request('GET', '/api/experiments')
    assert ret == []

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)

    ret = await client.request('GET', '/api/experiments')
    assert ret == ['IceCube']

@pytest.mark.asyncio
async def test_institutions(server):
    rest, token, *_ = server
    client = await rest('test')

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    
    ret = await client.request('GET', '/api/experiments/IceCube/institutions')
    assert ret == []

    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    ret = await client.request('GET', '/api/experiments/IceCube/institutions')
    assert ret == ['UW-Madison']

@pytest.mark.asyncio
async def test_inst_approvals_register(server, mongo_client):
    _, token, address, *_ = server
    session = AsyncSession(retries=0)

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    with pytest.raises(Exception):
        r = await asyncio.wrap_future(session.post(address+'/api/inst_approvals'))
        r.raise_for_status()

    data = {
        'experiment': 'IceCube',
        'institution': 'UW-Madison',
        'first_name': 'first',
        'last_name': 'last',
        'email': 'test@test',
    }
    r = await asyncio.wrap_future(session.post(address+'/api/inst_approvals', json=data))
    r.raise_for_status()
    ret = r.json()
    approval_id = ret['id']

    ret = await mongo_client.user_registrations.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['first_name'] == data['first_name']

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id
    assert ret[0]['experiment'] == data['experiment']
    assert ret[0]['institution'] == data['institution']

@pytest.mark.asyncio
async def test_inst_approvals_second(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    client = await rest('test')

    with pytest.raises(Exception):
        await client.request('POST', '/api/inst_approvals')

    data = {
        'experiment': 'IceCube',
        'institution': 'UW-Madison',
    }
    ret = await client.request('POST', '/api/inst_approvals', data)
    approval_id = ret['id']

    ret = await mongo_client.user_registrations.find().to_list(10)
    assert len(ret) == 0

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id
    assert ret[0]['experiment'] == data['experiment']
    assert ret[0]['institution'] == data['institution']
    assert ret[0]['username'] == 'test'

@pytest.mark.asyncio
async def test_inst_approvals_move(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    await krs.groups.create_group('/institutions/IceCube/OldInst', token=token)
    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    client = await rest('test', groups=['/institutions/IceCube/OldInst'])

    with pytest.raises(Exception):
        await client.request('POST', '/api/inst_approvals')

    data = {
        'experiment': 'IceCube',
        'institution': 'UW-Madison',
        'remove_institution': 'OldInst',
    }
    ret = await client.request('POST', '/api/inst_approvals', data)
    approval_id = ret['id']

    ret = await mongo_client.user_registrations.find().to_list(10)
    assert len(ret) == 0

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id
    assert ret[0]['experiment'] == data['experiment']
    assert ret[0]['institution'] == data['institution']
    assert ret[0]['remove_institution'] == data['remove_institution']
    assert ret[0]['username'] == 'test'

@pytest.mark.asyncio
async def test_inst_approvals_get(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    client = await rest('test')
    client2 = await rest('test2', groups=['/institutions/IceCube/UW-Madison/_admin'])

    data = {
        'experiment': 'IceCube',
        'institution': 'UW-Madison',
    }
    ret = await client.request('POST', '/api/inst_approvals', data)
    approval_id = ret['id']

    # no auth
    ret = await client.request('GET', '/api/inst_approvals')
    assert ret == []

    # success
    ret = await client2.request('GET', '/api/inst_approvals')

    assert len(ret) == 1
    assert ret[0]['id'] == approval_id
    assert ret[0]['experiment'] == data['experiment']
    assert ret[0]['institution'] == data['institution']
    assert ret[0]['username'] == 'test'

@pytest.mark.asyncio
async def test_inst_approvals_actions_approve(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    client = await rest('test')
    client2 = await rest('test2', groups=['/institutions/IceCube/UW-Madison/_admin'])

    data = {
        'experiment': 'IceCube',
        'institution': 'UW-Madison',
    }
    ret = await client.request('POST', '/api/inst_approvals', data)
    approval_id = ret['id']

    # no auth
    with pytest.raises(Exception):
        await client.request('POST', f'/api/inst_approvals/{approval_id}/actions/approve')

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id

    ret = await krs.groups.get_group_membership('/institutions/IceCube/UW-Madison', token=token)
    assert 'test' not in ret

    # success
    await client2.request('POST', f'/api/inst_approvals/{approval_id}/actions/approve')

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 0

    ret = await krs.groups.get_group_membership('/institutions/IceCube/UW-Madison', token=token)
    assert 'test' in ret

@pytest.mark.asyncio
async def test_inst_approvals_actions_deny(server, mongo_client):
    rest, token, *_ = server

    await krs.groups.create_group('/institutions', token=token)
    await krs.groups.create_group('/institutions/IceCube', token=token)
    await krs.groups.create_group('/institutions/IceCube/UW-Madison', token=token)

    client = await rest('test')
    client2 = await rest('test2', groups=['/institutions/IceCube/UW-Madison/_admin'])

    data = {
        'experiment': 'IceCube',
        'institution': 'UW-Madison',
    }
    ret = await client.request('POST', '/api/inst_approvals', data)
    approval_id = ret['id']

    # no auth
    with pytest.raises(Exception):
        await client.request('POST', f'/api/inst_approvals/{approval_id}/actions/deny')

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 1
    assert ret[0]['id'] == approval_id

    ret = await krs.groups.get_group_membership('/institutions/IceCube/UW-Madison', token=token)
    assert 'test' not in ret

    # success
    await client2.request('POST', f'/api/inst_approvals/{approval_id}/actions/deny')

    ret = await mongo_client.inst_approvals.find().to_list(10)
    assert len(ret) == 0

    ret = await krs.groups.get_group_membership('/institutions/IceCube/UW-Madison', token=token)
    assert 'test' not in ret

