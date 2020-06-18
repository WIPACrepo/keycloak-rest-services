import pytest

from krs.token import get_token
from krs import groups, users

from .util import keycloak_bootstrap

def test_list_groups(keycloak_bootstrap):
    # first test with no groups
    ret = groups.list_groups(token=keycloak_bootstrap)
    assert ret == {}

    # now test group hierarchy
    groups.create_group('/testgroup', token=keycloak_bootstrap)
    groups.create_group('/testgroup/testgroup2', token=keycloak_bootstrap)
    ret = groups.list_groups(token=keycloak_bootstrap)
    assert list(ret.keys()) == ['/testgroup','/testgroup/testgroup2']
    assert ret['/testgroup']['children'] == ['testgroup2']

def test_create_group(keycloak_bootstrap):
    groups.create_group('/testgroup', token=keycloak_bootstrap)

def test_create_subgroup(keycloak_bootstrap):
    groups.create_group('/testgroup', token=keycloak_bootstrap)
    groups.create_group('/testgroup/testgroup2', token=keycloak_bootstrap)

def test_delete_group(keycloak_bootstrap):
    # first test non-existing group
    groups.delete_group('/testgroup', token=keycloak_bootstrap)

    # now test existing group
    groups.create_group('/testgroup', token=keycloak_bootstrap)
    groups.delete_group('/testgroup', token=keycloak_bootstrap)

def test_get_user_groups(keycloak_bootstrap):
    with pytest.raises(Exception):
        groups.get_user_groups('testuser', token=keycloak_bootstrap)

    users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    ret = groups.get_user_groups('testuser', token=keycloak_bootstrap)
    assert ret == []

    groups.create_group('/testgroup', token=keycloak_bootstrap)
    groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)
    ret = groups.get_user_groups('testuser', token=keycloak_bootstrap)
    assert ret == ['/testgroup']

def test_add_user_group(keycloak_bootstrap):
    with pytest.raises(Exception):
        groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    with pytest.raises(Exception):
        groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    groups.create_group('/testgroup', token=keycloak_bootstrap)
    groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

def test_remove_user_group(keycloak_bootstrap):
    with pytest.raises(Exception):
        groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    users.create_user('testuser', 'first', 'last', 'email', token=keycloak_bootstrap)
    with pytest.raises(Exception):
        groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    groups.create_group('/testgroup', token=keycloak_bootstrap)

    # test for not being a member of the group
    groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)

    # now test for removing the group
    groups.add_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)
    groups.remove_user_group('/testgroup', 'testuser', token=keycloak_bootstrap)
    ret = groups.get_user_groups('testuser', token=keycloak_bootstrap)
    assert ret == []
