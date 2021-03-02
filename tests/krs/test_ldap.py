import pytest
import ldap3
from ldap3 import Server, Connection, ALL

from krs import ldap


@pytest.fixture
def ldap_bootstrap(monkeypatch):
    monkeypatch.setenv('LDAP_USER_BASE', 'ou=peopleTest,dc=icecube,dc=wisc,dc=edu')

    obj = ldap.LDAP()
    config = obj.config

    c = Connection(config['LDAP_URL'], user=config['LDAP_ADMIN_USER'], password=config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

    def cleanup():
        ret = c.search(config["LDAP_USER_BASE"], '(uid=*)', attributes=['uid'])
        if ret:
            uids = [e['uid'] for e in c.entries]
            for uid in uids:
                c.delete(f'uid={uid},{config["LDAP_USER_BASE"]}')
        c.delete(config["LDAP_USER_BASE"])
    cleanup()

    c.add(config["LDAP_USER_BASE"], ['organizationalUnit', 'top'],
        {
            'ou': 'peopleTest',
        }
    )

    try:
        yield obj
    finally:
        cleanup()

def test_get_users_none(ldap_bootstrap):
    with pytest.raises(KeyError):
        ldap_bootstrap.get_user('foo')

def test_create_user(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')

    ret = ldap_bootstrap.get_user('foo')
    assert ret['uid'] == 'foo'
    assert ret['givenName'] == 'foo'
    assert ret['sn'] == 'bar'
    assert ret['mail'] == 'foo@bar'

def test_create_user_fail(ldap_bootstrap):
    with pytest.raises(Exception):
        ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar')

    with pytest.raises(KeyError):
        ldap_bootstrap.get_user('foo')

def test_modify_user_class(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234, 'homeDirectory': f'/home/foo'}, objectClass='posixAccount')
    ret = ldap_bootstrap.get_user('foo')
    assert ret['gidNumber'] == 1234
    assert 'posixAccount' in ret['objectClass']

def test_modify_user_remove_class(ldap_bootstrap):
    ldap_bootstrap.create_user(username='foo', firstName='foo', lastName='bar', email='foo@bar')
    ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234, 'homeDirectory': f'/home/foo'}, objectClass='posixAccount')
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

    ldap_bootstrap.modify_user('foo', {'gidNumber': 1234, 'uidNumber': 1234, 'homeDirectory': f'/home/foo'}, objectClass='posixAccount')
    with pytest.raises(Exception):
        # cannot remove objectClass without removing attrs
        ldap_bootstrap.modify_user('foo', removeObjectClass='posixAccount')
