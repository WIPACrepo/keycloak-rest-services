# noinspection PyPackageRequirements
import pytest

from krs import users

from ..util import keycloak_bootstrap


@pytest.mark.asyncio
async def test_list_users_empty(keycloak_bootstrap):
    ret = await users.list_users(rest_client=keycloak_bootstrap)
    assert ret == {}


# noinspection LongLine
@pytest.mark.asyncio
async def test_list_users(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    ret = await users.list_users(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['testuser']
    assert ret['testuser']['firstName'] == 'first'
    assert ret['testuser']['lastName'] == 'last'
    assert ret['testuser']['email'] == 'foo@test'


# krs.users.list_users()'s query validation is based in part on assumptions about
# version-specific behavior of Keycloak. Some of this assumed behavior is problematic
# from the operational standpoint and could be result of bugs that prevent certain
# valid attribute keys/values to be queried using the /users q= API. The purpose of
# this test is to confirm out-of-band that the *reasonable* queries blocked by the
# validation code of krs.users.list_users() indeed don't work correctly with the
# version of Keycloak being tested. If this test fails, krs.users.list_users()'s
# query *validation* logic needs to be updated to allow the type of query in question
# (proper handling of the query should be tested elsewhere)
# noinspection LongLine
@pytest.mark.asyncio
async def test_important_user_attr_query_quirks(keycloak_bootstrap):
    await users.create_user('user', first_name='f', last_name='l', email='user@test',
                            attribs={'colon:in:key': 1}, rest_client=keycloak_bootstrap)
    # Query format buried here: https://www.keycloak.org/docs-api/26.0.6/rest-api/index.html
    res = await keycloak_bootstrap.request('GET', '/users?q="colon:in:key":1')
    assert not res


# noinspection LongLine
@pytest.mark.asyncio
async def test_list_user_attr_query_simple(keycloak_bootstrap):
    await users.create_user('mult_attrs_match1', first_name='f', last_name='l', email='7@test',
                            attribs={'mult1': 1, 'mult2': 2}, rest_client=keycloak_bootstrap)
    await users.create_user('mult_attrs_match2', first_name='f', last_name='l', email='8@test',
                            attribs={'mult1': 1, 'mult2': 2}, rest_client=keycloak_bootstrap)
    await users.create_user('mult_attrs_non_match', first_name='f', last_name='l', email='9@test',
                            attribs={'mult1': 1, 'mult2': 999}, rest_client=keycloak_bootstrap)

    ret = await users.list_users(attr_query={'mult1': 1, 'mult2': 2}, rest_client=keycloak_bootstrap)
    assert sorted(ret.keys()) == ['mult_attrs_match1', 'mult_attrs_match2']


# Construct "tricky" user attribute query keys and values that are valid,
# but need to be handled with care by krs.users.list_users() (simple cases
# should be tested from test_list_user_attr_query_simple(). The intention
# here is not to be exhaustive and try to detect every minute change in
# behavior between Keycloak's versions, but to only test for edge cases
# that are reasonable (e.g. as of Keycloak 24.0.3 "  " is a valid key, but
# don't test for it because using such a key is not super smart).
valid_tricky_attr_query_keys = [' beginning_with_space',
                                'ending_with_space ',
                                'containing space',
                                "'single-quoted string'"]
valid_tricky_attr_query_values = ['a:b may_cause_ambiguity'] + valid_tricky_attr_query_keys


# noinspection LongLine
@pytest.mark.parametrize('key', valid_tricky_attr_query_keys)
@pytest.mark.asyncio
async def test_list_user_attr_query_tricky_valid_key(key, keycloak_bootstrap):
    await users.create_user('user', first_name='f', last_name='l', email='user@test',
                            attribs={key: 'value'}, rest_client=keycloak_bootstrap)
    ret = await users.list_users(attr_query={key: 'value'}, rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['user']


# noinspection LongLine
@pytest.mark.parametrize('value', valid_tricky_attr_query_values)
@pytest.mark.asyncio
async def test_list_user_attr_query_tricky_valid_value(value, keycloak_bootstrap):
    await users.create_user('user', first_name='f', last_name='l', email='user@test',
                            attribs={'key': value}, rest_client=keycloak_bootstrap)
    ret = await users.list_users(attr_query={'key': value}, rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['user']


# Construct user attribute query keys and values that are either inherently
# invalid, or may not be formatted correctly by krs.users.list_users(), or are
# handled inconsistently by different versions of Keycloak, and so should be
# rejected by krs.users.list_users(). Only test for reasonable cases. If you
# use "  " as a value, there is no helping you.
problematic_attr_query_keys = [':a', 'a&a', 'a"a']
problematic_attr_query_values = ['a&a', 'a"a']


# noinspection LongLine
@pytest.mark.parametrize('key', problematic_attr_query_keys)
@pytest.mark.asyncio
async def test_list_user_attr_query_problematic_keys(key, keycloak_bootstrap):
        await users.create_user(f'bad', first_name='f', last_name='l', email=f'bad@test',
                                attribs={key: "value"}, rest_client=keycloak_bootstrap)
        with pytest.raises(NotImplementedError):
            assert not await users.list_users(attr_query={key: "value"}, rest_client=keycloak_bootstrap)


# noinspection LongLine
@pytest.mark.parametrize('value', problematic_attr_query_values)
@pytest.mark.asyncio
async def test_list_user_attr_query_problematic_values(value, keycloak_bootstrap):
    await users.create_user(f'bad', first_name='f', last_name='l', email=f'bad@test',
                            attribs={"key": value}, rest_client=keycloak_bootstrap)
    with pytest.raises(NotImplementedError):
        assert not await users.list_users(attr_query={"key": value}, rest_client=keycloak_bootstrap)


# noinspection LongLine
@pytest.mark.asyncio
async def test_user_info(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['firstName'] == 'first'
    assert ret['lastName'] == 'last'
    assert ret['email'] == 'foo@test'


# noinspection LongLine
@pytest.mark.asyncio
async def test_create_user(keycloak_bootstrap):
    await users.create_user('testuser', first_name='Fĭrst', last_name='Mü Lăst', email='foo@test', rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'canonical_email': 'first.mu.last@icecube.wisc.edu'}


# noinspection LongLine
@pytest.mark.asyncio
async def test_create_user_same_names(keycloak_bootstrap):
    await users.create_user('same-name-1', first_name='Fĭrst', last_name='Mü Lăst', email='foo1@test', rest_client=keycloak_bootstrap)
    await users.create_user('same-name-2', first_name='Fĭrst', last_name='Mü Lăst', email='foo2@test', rest_client=keycloak_bootstrap)
    user1 = await users.user_info('same-name-1', rest_client=keycloak_bootstrap)
    assert user1['attributes']['canonical_email'] == 'first.mu.last@icecube.wisc.edu'
    user2 = await users.user_info('same-name-2', rest_client=keycloak_bootstrap)
    assert user2['attributes']['canonical_email'] != 'first.mu.last@icecube.wisc.edu'
    assert user2['attributes']['canonical_email'].startswith('first.mu.last')


# noinspection LongLine
@pytest.mark.asyncio
async def test_modify_user(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs={'foo': 'bar'}, rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'foo' in ret['attributes']
    assert ret['attributes']['foo'] == 'bar'


# noinspection LongLine
# noinspection PyTypeChecker
@pytest.mark.asyncio
async def test_modify_user_asserts(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    with pytest.raises(RuntimeError):
        await users.modify_user('testuser', {'foo': 'bar'}, rest_client=keycloak_bootstrap)
    with pytest.raises(RuntimeError):
        await users.modify_user('testuser', first_name={'foo': 'bar'}, rest_client=keycloak_bootstrap)
    with pytest.raises(RuntimeError):
        await users.modify_user('testuser', last_name={'foo': 'bar'}, rest_client=keycloak_bootstrap)
    with pytest.raises(RuntimeError):
        await users.modify_user('testuser', email={'foo': 'bar'}, rest_client=keycloak_bootstrap)


# noinspection LongLine
# noinspection PyPep8Naming
@pytest.mark.asyncio
async def test_modify_user_firstName(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', first_name='bar', rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['firstName'] == 'bar'


# noinspection LongLine
# noinspection PyPep8Naming
@pytest.mark.asyncio
async def test_modify_user_lastName(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', last_name='bar', rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['lastName'] == 'bar'


# noinspection LongLine
@pytest.mark.asyncio
async def test_modify_user_email(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', email='bar@test', rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['email'] == 'bar@test'


# noinspection LongLine
@pytest.mark.asyncio
async def test_modify_user_existing_attr(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs={'foo': 'bar'}, rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs={'baz': 'foo'}, rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': 'bar', 'baz': 'foo', 'canonical_email': 'first.last@icecube.wisc.edu'}


# noinspection LongLine
@pytest.mark.asyncio
async def test_modify_user_attr_list(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs={'foo': ['bar', 'baz']}, rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs={'baz': [1, 2, 3]}, rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'foo': ['bar', 'baz'], 'baz': ['1', '2', '3'], 'canonical_email': 'first.last@icecube.wisc.edu'}


# noinspection LongLine
@pytest.mark.asyncio
async def test_modify_user_del_attr(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', attribs={'foo': 'bar'}, rest_client=keycloak_bootstrap)
    await users.modify_user('testuser', attribs={'foo': None, 'baz': 'foo'}, rest_client=keycloak_bootstrap)
    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert ret['attributes'] == {'baz': 'foo', 'canonical_email': 'first.last@icecube.wisc.edu'}


# noinspection LongLine
@pytest.mark.asyncio
async def test_set_user_password(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.set_user_password('testuser', 'foo', rest_client=keycloak_bootstrap)


# noinspection LongLine
@pytest.mark.asyncio
async def test_set_user_password_bad(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    with pytest.raises(Exception):
        # noinspection PyTypeChecker
        await users.set_user_password('testuser', ['f', 'o', 'o'], rest_client=keycloak_bootstrap)


# noinspection LongLine
@pytest.mark.asyncio
async def test_delete_user(keycloak_bootstrap):
    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.delete_user('testuser', rest_client=keycloak_bootstrap)
