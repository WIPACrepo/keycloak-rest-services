import pytest

from krs import ldap

from ..util import ldap_bootstrap


def test_get_users_none(ldap_bootstrap):
    with pytest.raises(KeyError):
        ldap_bootstrap.get_user('foo')

def test_list_users_none(ldap_bootstrap):
    ret = ldap_bootstrap.list_users()
    assert not ret

def test_create_user(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')

    ret = ldap_bootstrap.get_user('foo')
    assert ret['uid'] == 'foo'
    assert ret['givenName'] == 'foo'
    assert ret['sn'] == 'bar'
    assert ret['mail'] == 'foo@bar'

def test_list_users(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')

    ret = ldap_bootstrap.list_users()
    assert len(ret) == 1
    assert 'foo' in ret
    assert ret['foo']['uid'] == 'foo'
    assert ret['foo']['givenName'] == 'foo'
    assert ret['foo']['sn'] == 'bar'
    assert ret['foo']['mail'] == 'foo@bar'

def test_list_users_attrs(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')

    ret = ldap_bootstrap.list_users(['sn'])
    assert len(ret) == 1
    assert 'foo' in ret
    assert ret['foo']['sn'] == 'bar'
    assert 'uid' not in ret['foo']

def test_create_user_fail(ldap_bootstrap):
    with pytest.raises(Exception):
        ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar')

    with pytest.raises(KeyError):
        ldap_bootstrap.get_user('foo')

def test_modify_user_class(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234, 'homeDirectory': '/home/foo'}, objectClass='posixAccount')
    ret = ldap_bootstrap.get_user('foo')
    assert ret['gidNumber'] == 1234
    assert 'posixAccount' in ret['objectClass']

def test_modify_user_remove_class(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234, 'homeDirectory': '/home/foo'}, objectClass='posixAccount')
    ldap_bootstrap.modify_user('foo', {'gidNumber': None, 'uidNumber': None, 'homeDirectory': None}, removeObjectClass='posixAccount')
    ret = ldap_bootstrap.get_user('foo')
    assert 'gidNumber' not in ret
    assert 'posixAccount' not in ret['objectClass']

def test_modify_user_attrs(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.modify_user('foo', {'givenName': 'foofoo'})
    ret = ldap_bootstrap.get_user('foo')
    assert ret['givenName'] == 'foofoo'

def test_modify_user_fail(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')

    with pytest.raises(Exception):
        # missing homeDirectory for posixAccount
        ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234}, objectClass='posixAccount')

    ret = ldap_bootstrap.get_user('foo')
    assert 'gidNumber' not in ret

    with pytest.raises(Exception):
        # cannot add field gidNumber with current objectClasses
        ldap_bootstrap.modify_user('foo', {'gidNumber': 1234})

    ret = ldap_bootstrap.get_user('foo')
    assert 'gidNumber' not in ret

    ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234, 'homeDirectory': '/home/foo'}, objectClass='posixAccount')
    with pytest.raises(Exception):
        # cannot remove objectClass without removing attrs
        ldap_bootstrap.modify_user('foo', removeObjectClass='posixAccount')

def test_create_group(ldap_bootstrap):
    ldap_bootstrap.create_group('foo')
    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']

def test_list_group(ldap_bootstrap):
    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == []

def test_add_user_group(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo')
    ldap_bootstrap.add_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    assert any(member.startswith('uid=foo,') for member in ret['foo']['member'])

def test_add_user_group_twice(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo')
    ldap_bootstrap.add_user_group('foo', 'foo')
    ldap_bootstrap.add_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    assert 1 == sum(1 for member in ret['foo']['member'] if member.startswith('uid=foo,'))

def test_remove_user_group(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo')
    ldap_bootstrap.add_user_group('foo', 'foo')
    ldap_bootstrap.remove_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    print(ret)
    assert not any(member.startswith('uid=foo,') for member in ret['foo']['member'])

def test_remove_user_group_twice(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo')
    ldap_bootstrap.add_user_group('foo', 'foo')
    ldap_bootstrap.remove_user_group('foo', 'foo')
    ldap_bootstrap.remove_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    print(ret)
    assert not any(member.startswith('uid=foo,') for member in ret['foo']['member'])

def test_create_group_posix(ldap_bootstrap):
    ldap_bootstrap.create_group('foo', gidNumber=1000)
    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']

def test_add_user_group_posix(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo', gidNumber=1000)
    ldap_bootstrap.add_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    assert 'foo' in ret['foo']['memberUid']

def test_add_user_group_posix_twice(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo', gidNumber=1000)
    ldap_bootstrap.add_user_group('foo', 'foo')
    ldap_bootstrap.add_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    print(ret)
    assert list(ret.keys()) == ['foo']
    if isinstance(ret['foo']['memberUid'], str):
        assert 'foo' in ret['foo']['memberUid']
    else:
        assert 1 == sum(1 for member in ret['foo']['memberUid'] if member == 'foo')

def test_remove_user_group_posix(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo', gidNumber=1000)
    ldap_bootstrap.add_user_group('foo', 'foo')
    ldap_bootstrap.remove_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    print(ret)
    assert 'memberUid' not in ret['foo'] or 'foo' not in ret['foo']['memberUid']

def test_remove_user_group_posix_twice(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.create_group('foo', gidNumber=1000)
    ldap_bootstrap.add_user_group('foo', 'foo')
    ldap_bootstrap.remove_user_group('foo', 'foo')
    ldap_bootstrap.remove_user_group('foo', 'foo')

    ret = ldap_bootstrap.list_groups()
    assert list(ret.keys()) == ['foo']
    print(ret)
    assert 'memberUid' not in ret['foo'] or 'foo' not in ret['foo']['memberUid']
