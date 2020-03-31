from krs.token import get_token
from krs import users

from .util import keycloak_bootstrap

def test_list_users_empty(keycloak_bootstrap):
    ret = users.list_users(token=keycloak_bootstrap)
    assert ret == {}
    
def test_list_users(keycloak_bootstrap):
    users.create_user('testuser', first_name='first', last_name='last', email='foo@test', token=keycloak_bootstrap)
    ret = users.list_users(token=keycloak_bootstrap)
    assert list(ret.keys()) == ['testuser']
    assert ret['testuser']['firstName'] == 'first'
    assert ret['testuser']['lastName'] == 'last'
    assert ret['testuser']['email'] == 'foo@test'
    
def test_user_info(keycloak_bootstrap):
    users.create_user('testuser', first_name='first', last_name='last', email='foo@test', token=keycloak_bootstrap)
    ret = users.user_info('testuser', token=keycloak_bootstrap)
    assert ret['firstName'] == 'first'
    assert ret['lastName'] == 'last'
    assert ret['email'] == 'foo@test'

def test_create_user(keycloak_bootstrap):
    users.create_user('testuser', first_name='first', last_name='last', email='foo@test', token=keycloak_bootstrap)

def test_delete_user(keycloak_bootstrap):
    users.create_user('testuser', first_name='first', last_name='last', email='foo@test', token=keycloak_bootstrap)
    users.delete_user('testuser', token=keycloak_bootstrap)
