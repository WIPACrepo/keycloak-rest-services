import pytest
import asyncio
import logging
import time

#from krs.token import get_token
from krs import users, groups, bootstrap  
from actions import create_posix_account
from actions import ldap_password_exp_email

from ..util import keycloak_bootstrap, ldap_bootstrap, rabbitmq_bootstrap


@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)
    await users.set_user_password('testuser', 'test', rest_client=keycloak_bootstrap)

    # initially user should be up to date
    ldap_users = ldap_bootstrap.list_users()
    e1, e2, d = await ldap_password_exp_email._get_expired_users(ldap_users, ['testuser'])

    assert not e1
    assert not e2
    assert not d

    # test expiring user
    today = int(time.time()/3600/24)
    ldap_bootstrap.modify_user('testuser', attributes={'shadowExpire': today+10})
    
    ldap_users = ldap_bootstrap.list_users()
    e1, e2, d = await ldap_password_exp_email._get_expired_users(ldap_users, ['testuser'])

    assert 'testuser' in e1
    assert not e2
    assert not d
    
    # test expired user
    ldap_bootstrap.modify_user('testuser', attributes={'shadowExpire': today})
    
    ldap_users = ldap_bootstrap.list_users()
    e1, e2, d = await ldap_password_exp_email._get_expired_users(ldap_users, ['testuser'])

    assert not e1
    assert 'testuser' in e2
    assert not d
    
    # test "disabled" user
    ldap_bootstrap.modify_user('testuser', attributes={'shadowExpire': today-365})
    
    ldap_users = ldap_bootstrap.list_users()
    e1, e2, d = await ldap_password_exp_email._get_expired_users(ldap_users, ['testuser'])

    assert not e1
    assert not e2
    assert 'testuser' in d
