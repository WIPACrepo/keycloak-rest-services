import pytest

from krs.token import get_token
from krs import groups, users

from ..util import keycloak_bootstrap

@pytest.mark.asyncio
async def test_list_groups(keycloak_bootstrap):
    # first test with no groups
    ret = await groups.list_groups(rest_client=keycloak_bootstrap)
    assert ret == {}

    # now test group hierarchy
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', rest_client=keycloak_bootstrap)
    ret = await groups.list_groups(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['/testgroup','/testgroup/testgroup2']
    assert ret['/testgroup']['children'] == ['testgroup2']

@pytest.mark.asyncio
async def test_group_info(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['name'] == 'testgroup'
    assert ret['path'] == '/testgroup'
    assert [g['name'] for g in ret['subGroups']] == ['testgroup2']

@pytest.mark.asyncio
async def test_group_attrs(keycloak_bootstrap):
    await groups.create_group('/testgroup', attrs={'foo':'bar'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['name'] == 'testgroup'
    assert ret['path'] == '/testgroup'
    assert ret['attributes'] == {'foo': 'bar'}

@pytest.mark.asyncio
async def test_modify_group(keycloak_bootstrap):
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {}

    await groups.modify_group('/testgroup', {'baz': 'foo'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'baz': 'foo'}

@pytest.mark.asyncio
async def test_modify_group_with_attrs(keycloak_bootstrap):
    await groups.create_group('/testgroup', attrs={'foo':'bar'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': 'bar'}

    await groups.modify_group('/testgroup', {'baz': 'foo'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': 'bar', 'baz': 'foo'}

@pytest.mark.asyncio
async def test_modify_group_del_attr(keycloak_bootstrap):
    await groups.create_group('/testgroup', attrs={'foo':'bar'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': 'bar'}

    await groups.modify_group('/testgroup', {'foo': None, 'baz': 'foo'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'baz': 'foo'}

@pytest.mark.asyncio
async def test_group_info_by_id(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/testgroup', rest_client=keycloak_bootstrap)
    group_id = ret['id']
    ret = await groups.group_info_by_id(group_id, rest_client=keycloak_bootstrap)
    assert ret['name'] == 'testgroup'
    assert ret['path'] == '/testgroup'
    assert [g['name'] for g in ret['subGroups']] == ['testgroup2']

@pytest.mark.asyncio
async def test_create_group(keycloak_bootstrap):
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_create_subgroup(keycloak_bootstrap):
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_delete_group(keycloak_bootstrap):
    # first test non-existing group
    await groups.delete_group('/testgroup', rest_client=keycloak_bootstrap)

    # now test existing group
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.delete_group('/testgroup', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_get_user_groups(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.get_user_groups('testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', rest_client=keycloak_bootstrap)
    assert ret == []

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', rest_client=keycloak_bootstrap)
    assert ret == ['/testgroup']

@pytest.mark.asyncio
async def test_add_user_group(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_remove_user_group(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.remove_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    with pytest.raises(Exception):
        await groups.remove_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)

    # test for not being a member of the group
    await groups.remove_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    # now test for removing the group
    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)
    await groups.remove_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', rest_client=keycloak_bootstrap)
    assert ret == []

@pytest.mark.asyncio
async def test_get_group_membership(keycloak_bootstrap):
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    with pytest.raises(Exception):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    ret = await groups.get_group_membership('/testgroup', rest_client=keycloak_bootstrap)
    assert ret == []

    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    ret = await groups.get_group_membership('/testgroup', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']

@pytest.mark.asyncio
async def test_parent_child_group_membership(keycloak_bootstrap):
    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    await groups.create_group('/parent', rest_client=keycloak_bootstrap)
    await groups.create_group('/parent/child', rest_client=keycloak_bootstrap)

    await groups.add_user_group('/parent', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/parent/child', 'testuser', rest_client=keycloak_bootstrap)

    ret = await groups.get_group_membership('/parent', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']
    ret = await groups.get_group_membership('/parent/child', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']

@pytest.mark.asyncio
async def test_child_parent_group_membership(keycloak_bootstrap):
    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    await groups.create_group('/parent', rest_client=keycloak_bootstrap)
    await groups.create_group('/parent/child', rest_client=keycloak_bootstrap)

    await groups.add_user_group('/parent/child', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/parent', 'testuser', rest_client=keycloak_bootstrap)

    ret = await groups.get_group_membership('/parent', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']
    ret = await groups.get_group_membership('/parent/child', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']

@pytest.mark.asyncio
async def test_add_user_group_multiple(keycloak_bootstrap):
    await users.create_user('testuser', 'first', 'last', 'email', rest_client=keycloak_bootstrap)
    await groups.create_group('/foo', rest_client=keycloak_bootstrap)
    await groups.create_group('/foo/bar', rest_client=keycloak_bootstrap)
    await groups.create_group('/bar', rest_client=keycloak_bootstrap)
    await groups.create_group('/foo/bar/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/bar/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)

    await groups.add_user_group('/foo/bar/testgroup', 'testuser', rest_client=keycloak_bootstrap)


    ret = await groups.get_group_membership('/foo/bar/testgroup', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']
    ret = await groups.get_group_membership('/bar/testgroup', rest_client=keycloak_bootstrap)
    assert ret == []
    ret = await groups.get_group_membership('/testgroup', rest_client=keycloak_bootstrap)
    assert ret == []
