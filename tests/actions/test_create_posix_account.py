import asyncio
import logging
import pytest
import pytest_asyncio

#from krs.token import get_token
from krs import users, groups, bootstrap, rabbitmq
from actions import create_posix_account

from ..util import keycloak_bootstrap, ldap_bootstrap, rabbitmq_bootstrap


@pytest.mark.asyncio
async def test_create(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'homeDirectory' in ret['attributes']
    assert ret['attributes']['homeDirectory'] == '/home/testuser'
    assert 'loginShell' in ret['attributes']
    assert ret['attributes']['loginShell'] != '/sbin/nologin'

    ret2 = ldap_bootstrap.get_user('testuser')
    assert 'homeDirectory' in ret2
    assert ret2['homeDirectory'] == '/home/testuser'
    assert 'posixAccount' in ret2['objectClass']

    ret3 = ldap_bootstrap.get_group('testuser')
    assert ret3['gidNumber'] == ret2['gidNumber'] == int(ret['attributes']['gidNumber'])

@pytest.mark.asyncio
async def test_not_in_group(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)

    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'homeDirectory' not in ret['attributes']

    ret = ldap_bootstrap.get_user('testuser')
    assert 'homeDirectory' not in ret
    assert 'posixAccount' not in ret['objectClass']

@pytest.mark.asyncio
async def test_invalid_group(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)

    with pytest.raises(groups.GroupDoesNotExist):
        await create_posix_account.process('/foofoo', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

@pytest.mark.asyncio
async def test_create_remove(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.remove_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'homeDirectory' in ret['attributes']
    assert ret['attributes']['homeDirectory'] == '/home/testuser'
    assert 'loginShell' in ret['attributes']
    assert ret['attributes']['loginShell'] == '/sbin/nologin'

@pytest.mark.asyncio
async def test_create_remove_add(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.remove_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'homeDirectory' in ret['attributes']
    assert ret['attributes']['homeDirectory'] == '/home/testuser'
    assert 'loginShell' in ret['attributes']
    assert ret['attributes']['loginShell'] != '/sbin/nologin'

@pytest.mark.asyncio
async def test_create_extra_groups(keycloak_bootstrap, ldap_bootstrap):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap)

    ldap_bootstrap.create_group('foo', gidNumber=1234)
    await create_posix_account.process('/posix', keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)

    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    assert 'homeDirectory' in ret['attributes']
    assert ret['attributes']['homeDirectory'] == '/home/testuser'
    assert 'loginShell' in ret['attributes']
    assert ret['attributes']['loginShell'] != '/sbin/nologin'
    assert 'gidNumber' in ret['attributes']
    assert ret['attributes']['gidNumber'] == '1235'

    ret = ldap_bootstrap.get_user('testuser')
    assert 'homeDirectory' in ret
    assert ret['homeDirectory'] == '/home/testuser'
    assert 'posixAccount' in ret['objectClass']

@pytest_asyncio.fixture
async def listener(keycloak_bootstrap, ldap_bootstrap, rabbitmq_bootstrap):
    mq = create_posix_account.listener('/posix', dedup=None, keycloak_client=keycloak_bootstrap, ldap_client=ldap_bootstrap)
    await mq.start()
    try:
        yield mq
    finally:
        await mq.stop()

@pytest.mark.asyncio
async def test_listener(keycloak_bootstrap, ldap_bootstrap, listener):
    await ldap_bootstrap.keycloak_ldap_link(bootstrap.get_token())

    await users.create_user('testuser', first_name='first', last_name='last', email='foo@test', rest_client=keycloak_bootstrap)
    await groups.create_group('/posix', rest_client=keycloak_bootstrap)

    await groups.add_user_group('/posix', 'testuser', rest_client=keycloak_bootstrap) # triggers listener

    await asyncio.sleep(.5) # allow listener to run

    ret = await users.user_info('testuser', rest_client=keycloak_bootstrap)
    logging.info(f'{ret}')
    assert 'homeDirectory' in ret['attributes']
    assert ret['attributes']['homeDirectory'] == '/home/testuser'

    ret = ldap_bootstrap.get_user('testuser')
    assert 'homeDirectory' in ret
    assert ret['homeDirectory'] == '/home/testuser'
    assert 'posixAccount' in ret['objectClass']
