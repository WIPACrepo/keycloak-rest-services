import pytest

from krs.token import get_token
from krs import groups, users

from ..util import keycloak_bootstrap

@pytest.mark.asyncio
async def test_list_groups(keycloak_bootstrap):
    # first test with no groups
    ret = await groups.list_groups(token=keycloak_bootstrap)
    assert ret == {}

    # now test group hierarchy
    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', token=keycloak_bootstrap)
    ret = await groups.list_groups(token=keycloak_bootstrap)
    assert list(ret.keys()) == ['/testgroup','/testgroup/testgroup2']
    assert ret['/testgroup']['children'] == ['testgroup2']

@pytest.mark.asyncio
async def test_group_info(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.group_info('/testgroup', token=keycloak_bootstrap)

    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', token=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', token=keycloak_bootstrap)
    assert ret['name'] == 'testgroup'
    assert ret['path'] == '/testgroup'
    assert [g['name'] for g in ret['subGroups']] == ['testgroup2']

@pytest.mark.asyncio
async def test_group_info_by_id(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.group_info('/testgroup', token=keycloak_bootstrap)

    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', token=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', token=keycloak_bootstrap)
    group_id = ret['id']
    ret = await groups.group_info_by_id(group_id, token=keycloak_bootstrap)
    assert ret['name'] == 'testgroup'
    assert ret['path'] == '/testgroup'
    assert [g['name'] for g in ret['subGroups']] == ['testgroup2']

@pytest.mark.asyncio
async def test_create_group(keycloak_bootstrap):
    await groups.create_group('/testgroup', token=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_create_subgroup(keycloak_bootstrap):
    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', token=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_delete_group(keycloak_bootstrap):
    # first test non-existing group
    await groups.delete_group('/testgroup', token=keycloak_bootstrap)

    # now test existing group
    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.delete_group('/testgroup', token=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_get_user_groups(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.get_user_groups('testuser', token=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', token=keycloak_bootstrap)
    assert ret == []

    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', token=keycloak_bootstrap)
    assert ret == ['/testgroup']

@pytest.mark.asyncio
async def test_add_user_group(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_remove_user_group(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    with pytest.raises(Exception):
        await groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    await groups.create_group('/testgroup', token=keycloak_bootstrap)

    # test for not being a member of the group
    await groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    # now test for removing the group
    await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)
    await groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', token=keycloak_bootstrap)
    assert ret == []

@pytest.mark.asyncio
async def test_get_group_membership(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    await groups.create_group('/testgroup', token=keycloak_bootstrap)
    ret = await groups.get_group_membership('/testgroup', token=keycloak_bootstrap)
    assert ret == []
    
    await groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    ret = await groups.get_group_membership('/testgroup', token=keycloak_bootstrap)
    assert ret == ['testuser']
