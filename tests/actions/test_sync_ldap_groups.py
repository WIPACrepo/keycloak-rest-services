import pytest
import asyncio
import logging

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
from actions import create_posix_account, sync_ldap_groups

from ..util import keycloak_bootstrap, ldap_bootstrap, rabbitmq_bootstrap


def test_flatten_group_name():
    assert sync_ldap_groups.flatten_group_name('foo') == 'foo'
    assert sync_ldap_groups.flatten_group_name('foo/bar') == 'foo-bar'
    assert sync_ldap_groups.flatten_group_name('foo bar/baz') == 'foobar-baz'

def test_get_ldap_members_empty():
    assert sync_ldap_groups.get_ldap_members({}) == []

def test_get_ldap_members_uids_single():
    group = {'memberUid': 'foo'}
    assert sync_ldap_groups.get_ldap_members(group) == ['foo']

def test_get_ldap_members_single():
    group = {'member': ['cn=foo,ou=test,ou=com']}
    assert sync_ldap_groups.get_ldap_members(group) == ['foo']

def test_get_ldap_members_single_placeholder():
    group = {'member': ['cn=empty-membership-placeholder','cn=foo,ou=test,ou=com']}
    assert sync_ldap_groups.get_ldap_members(group) == ['foo']

def test_get_ldap_members_placeholder():
    group = {'member': ['cn=empty-membership-placeholder']}
    assert sync_ldap_groups.get_ldap_members(group) == []

@pytest.mark.asyncio
async def test_sync_posix_single_new(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix/test', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.add_user_group('/posix/test', 'testuser', rest_client=keycloak_bootstrap)
    await sync_ldap_groups.process('/posix', posix=True, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert 'gidNumber' in ret
    assert 'memberUid' in ret
    assert ret['memberUid'] == 'testuser'

@pytest.mark.asyncio
async def test_sync_posix_many_new(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.create_user('testuser2', first_name='first', last_name='last', email='foo2@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix/test', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser2', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.add_user_group('/posix/test', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix/test', 'testuser2', rest_client=keycloak_bootstrap)
    await sync_ldap_groups.process('/posix', posix=True, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert 'gidNumber' in ret
    assert 'memberUid' in ret
    assert set(ret['memberUid']) == set(['testuser', 'testuser2'])

@pytest.mark.asyncio
async def test_sync_posix_single_remove(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix/test', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ldap_bootstrap.create_group('test', gidNumber=2000)
    ldap_bootstrap.add_user_group('testuser', 'test')
    ret = ldap_bootstrap.get_group('test')
    assert 'gidNumber' in ret
    assert 'memberUid' in ret
    assert ret['memberUid'] == 'testuser'

    await sync_ldap_groups.process('/posix', posix=True, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert 'memberUid' not in ret

@pytest.mark.asyncio
async def test_sync_posix_many_new_remove(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.create_user('testuser2', first_name='first', last_name='last', email='foo2@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix/test', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser2', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ldap_bootstrap.create_group('test', gidNumber=2000)
    ldap_bootstrap.add_user_group('testuser', 'test')
    ret = ldap_bootstrap.get_group('test')
    assert 'gidNumber' in ret
    assert 'memberUid' in ret
    assert ret['memberUid'] == 'testuser'

    await groups.add_user_group('/posix/test', 'testuser2', rest_client=keycloak_bootstrap)
    await sync_ldap_groups.process('/posix', posix=True, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert ret['memberUid'] == 'testuser2'


@pytest.mark.asyncio
async def test_sync_group_single_new(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.create_group('/groups', rest_client=keycloak_bootstrap)
    await groups.create_group('/groups/test', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/groups/test', 'testuser', rest_client=keycloak_bootstrap)
    await sync_ldap_groups.process('/groups', posix=False, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert 'gidNumber' not in ret
    assert 'member' in ret
    assert 'uid=testuser,'+ldap_bootstrap.config['LDAP_USER_BASE'] in ret['member']

@pytest.mark.asyncio
async def test_sync_group_many_new(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.create_user('testuser2', first_name='first', last_name='last', email='foo2@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser2', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.create_group('/groups', rest_client=keycloak_bootstrap)
    await groups.create_group('/groups/test', rest_client=keycloak_bootstrap)
    await groups.create_group('/groups/test/foo', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/groups/test', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/groups/test', 'testuser2', rest_client=keycloak_bootstrap)
    await sync_ldap_groups.process('/groups', posix=False, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert 'gidNumber' not in ret
    assert 'member' in ret
    assert 'uid=testuser,'+ldap_bootstrap.config['LDAP_USER_BASE'] in ret['member']
    assert 'uid=testuser2,'+ldap_bootstrap.config['LDAP_USER_BASE'] in ret['member']

    with pytest.raises(KeyError):
        ret = ldap_bootstrap.get_group('test-foo')

@pytest.mark.asyncio
async def test_sync_group_recursive(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await users.create_user('testuser2', first_name='first', last_name='last', email='foo2@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser2', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.create_group('/groups', rest_client=keycloak_bootstrap)
    await groups.create_group('/groups/test', rest_client=keycloak_bootstrap)
    await groups.create_group('/groups/test/foo', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/groups/test', 'testuser', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/groups/test/foo', 'testuser2', rest_client=keycloak_bootstrap)
    await sync_ldap_groups.process('/groups', posix=False, recursive=True, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = ldap_bootstrap.get_group('test')
    print(ret)
    assert 'gidNumber' not in ret
    assert 'member' in ret
    assert 'uid=testuser,'+ldap_bootstrap.config['LDAP_USER_BASE'] in ret['member']

    ret = ldap_bootstrap.get_group('test-foo')
    print(ret)
    assert 'gidNumber' not in ret
    assert 'member' in ret
    assert 'uid=testuser2,'+ldap_bootstrap.config['LDAP_USER_BASE'] in ret['member']