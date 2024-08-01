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


# noinspection LongLine
@pytest.mark.asyncio
async def test_list_user_attr_query_transforms(keycloak_bootstrap):
    await users.create_user('spaces', first_name='f', last_name='l', email='spaces@test',
                            attribs={'_ _': '_ _'}, rest_client=keycloak_bootstrap)
    ret = await users.list_users(attr_query={'_ _': '_ _'}, rest_client=keycloak_bootstrap)
    assert sorted(ret.keys()) == ['spaces']

    await users.create_user('colons', first_name='f', last_name='l', email='colons@test',
                            attribs={':': ':'}, rest_client=keycloak_bootstrap)
    ret = await users.list_users(attr_query={':': ':'}, rest_client=keycloak_bootstrap)
    assert sorted(ret.keys()) == ['colons']


# noinspection LongLine
@pytest.mark.asyncio
async def test_list_user_attr_query_invalid(keycloak_bootstrap):
    bad_chars = "&'\""
    for i, char in enumerate(bad_chars):
        await users.create_user(f'attr_val_not_impl{i}', first_name='f', last_name='l', email=f'val-not-impl{i}@test',
                                attribs={'not_impl_val': f"{char}"}, rest_client=keycloak_bootstrap)
        with pytest.raises(NotImplementedError):
            assert not await users.list_users(attr_query={'not_impl_val': f"{char}"}, rest_client=keycloak_bootstrap)

        await users.create_user(f'attr_name_not_impl{i}', first_name='f', last_name='l', email=f'name-not-impl{i}@test',
                                attribs={f'{char}': 'not_impl_name'}, rest_client=keycloak_bootstrap)
        with pytest.raises(NotImplementedError):
            assert not await users.list_users(attr_query={f"{char}": "not_impl_name"}, rest_client=keycloak_bootstrap)


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
