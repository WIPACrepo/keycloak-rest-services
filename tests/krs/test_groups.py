import pytest

from krs.token import get_token
from krs import groups, users

from ..util import keycloak_bootstrap

@pytest.mark.asyncio
async def test_confirm_empty_subgroups_keycloak_quirk(keycloak_bootstrap):
    await groups.create_group('/group', rest_client=keycloak_bootstrap)
    await groups.create_group('/group/subgroup', rest_client=keycloak_bootstrap)
    ret = await keycloak_bootstrap.request(
        'GET', "/groups?briefRepresentation=false&populateHierarchy=true")
    if ret[0]['subGroups']:
        pytest.fail("""See full failure message.
It looks like bug where /groups incorrectly returns empty subgroups has been fixed
(see https://github.com/keycloak/keycloak/issues/27694).
This means that some functions that use the /groups endpoint unnecessarily apply
workarounds, which probably significantly slows them down.
 
At the time of writing these are the affected functions:

* group_info_by_id(): unnecessarily calls a function to populate subgroups,
                      which is quite slow.

* get_group_hierarchy(): unnecessarily inserts "search=" into the URL,
                         which probably slows it down.
""")

@pytest.mark.asyncio
async def test_list_groups_empty(keycloak_bootstrap):
    ret = await groups.list_groups(rest_client=keycloak_bootstrap)
    assert ret == {}

@pytest.mark.asyncio
async def test_list_groups(keycloak_bootstrap):
    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.create_group('/testgroup/testgroup2', rest_client=keycloak_bootstrap)
    ret = await groups.list_groups(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['/testgroup','/testgroup/testgroup2']
    assert ret['/testgroup']['children'] == ['testgroup2']

@pytest.mark.asyncio
async def test_group_info(keycloak_bootstrap):
    with pytest.raises(groups.GroupDoesNotExist):
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
async def test_modify_group_rename(keycloak_bootstrap):
    await groups.create_group('/parent', rest_client=keycloak_bootstrap)
    await groups.create_group('/parent/group', attrs={'foo':'bar'}, rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/parent/group', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': 'bar'}

    await groups.modify_group('/parent/group', new_group_name='group-new', rest_client=keycloak_bootstrap)
    ret = await groups.group_info('/parent/group-new', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': 'bar'}

@pytest.mark.asyncio
async def test_group_info_by_id(keycloak_bootstrap):
    with pytest.raises(groups.GroupDoesNotExist):
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

    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', rest_client=keycloak_bootstrap)
    assert ret == []

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)
    ret = await groups.get_user_groups('testuser', rest_client=keycloak_bootstrap)
    assert ret == ['/testgroup']

@pytest.mark.asyncio
async def test_add_user_group(keycloak_bootstrap):
    with pytest.raises(groups.GroupDoesNotExist):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
    with pytest.raises(groups.GroupDoesNotExist):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_remove_user_group(keycloak_bootstrap):
    with pytest.raises(groups.GroupDoesNotExist):
        await groups.remove_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
    with pytest.raises(groups.GroupDoesNotExist):
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
    with pytest.raises(groups.GroupDoesNotExist):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
    with pytest.raises(groups.GroupDoesNotExist):
        await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    await groups.create_group('/testgroup', rest_client=keycloak_bootstrap)
    ret = await groups.get_group_membership('/testgroup', rest_client=keycloak_bootstrap)
    assert ret == []

    await groups.add_user_group('/testgroup', 'testuser', rest_client=keycloak_bootstrap)

    ret = await groups.get_group_membership('/testgroup', rest_client=keycloak_bootstrap)
    assert ret == ['testuser']

@pytest.mark.asyncio
async def test_parent_child_group_membership(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
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
    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
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
    await users.create_user('testuser', first_name='first', last_name='last', email='email@test', rest_client=keycloak_bootstrap)
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


@pytest.mark.asyncio
async def test_get_group_hierarchy(keycloak_bootstrap):
    attrs = {'key':'value'}
    hierarchy = [
        {'name': 'a', 'path': '/a', 'subGroupCount': 2, 'attributes': attrs,
         'subGroups': [
             {'name': 'a-sub1', 'path': '/a/a-sub1', 'subGroupCount': 0, 'attributes': attrs, 'subGroups': []},
             {'name': 'a-sub2', 'path': '/a/a-sub2', 'subGroupCount': 0, 'attributes': attrs, 'subGroups': []},
         ]},
        {'name': 'b', 'path': '/b', 'subGroupCount': 1, 'attributes': attrs,
         'subGroups': [
             {'name': 'b-sub', 'path': '/b/b-sub', 'subGroupCount': 1, 'attributes': attrs,
              'subGroups': [
                  {'name': 'b-sub-sub', 'path': '/b/b-sub/b-sub-sub', 'subGroupCount': 0, 'attributes': attrs, 'subGroups': []},
              ]},
         ]},
        {'name': 'c', 'path': '/c', 'subGroupCount': 0, 'attributes': attrs, 'subGroups': []},
    ]

    await groups.create_group('/a', attrs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/a/a-sub1', attrs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/a/a-sub2', attrs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/b', attrs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/b/b-sub', attrs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/b/b-sub/b-sub-sub', attrs=attrs, rest_client=keycloak_bootstrap)
    await groups.create_group('/c', attrs=attrs, rest_client=keycloak_bootstrap)

    test_hierarchy = await groups.get_group_hierarchy(rest_client=keycloak_bootstrap)

    # subGroups are lists, but the problem is lists is that [1,2] != [2,1],
    # and subGroup lists can't be sorted. This function will convert subGroups
    # into dicts, which are easier to compare
    def replace_group_lists_with_dicts(arg):
        # make [{'name': 'foo', ...}, {'name': 'bar', ...}] into
        # {'foo': {'name': 'foo', ...}, 'bar': {'name': 'bar', ...}}
        ret = {}
        if isinstance(arg, list):
            for elt in arg:
                ret[elt['name']] = replace_group_lists_with_dicts(elt)
            return ret
        elif isinstance(arg, dict):
            for k in arg:
                ret[k] = replace_group_lists_with_dicts(arg[k])
            return ret
        else:
            return arg

    expected = replace_group_lists_with_dicts(hierarchy)
    actual = replace_group_lists_with_dicts(test_hierarchy)

    # recursive test if dict sub is contained in dict sup
    # assumes lists have been converted to dicts (above),
    def dict_is_contained(sub, sup):
        if isinstance(sub, dict):
            return all(dict_is_contained(sub[k], sup[k]) for k in sub)
        else:
            return sub == sup

    from pprint import pformat
    assert dict_is_contained(expected, actual), \
        f"{pformat(expected)}\n!=\n{pformat(actual)}"
