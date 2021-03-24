import pytest

from krs import ldap

from ..util import ldap_bootstrap


def test_get_users_none(ldap_bootstrap):
    with pytest.raises(KeyError):
        ldap_bootstrap.get_user('foo')

def test_list_users_none(ldap_bootstrap):
    # this raises because no user entries is conflated with a fatal operation
    with pytest.raises(Exception):
        ldap_bootstrap.list_users()

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
