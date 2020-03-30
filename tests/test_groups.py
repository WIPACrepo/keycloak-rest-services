from krs.token import get_token
from krs import groups

from .util import keycloak_bootstrap

def test_list_groups_empty(keycloak_bootstrap):
    ret = groups.list_groups(token=keycloak_bootstrap)
    assert ret == {}
    
def test_list_groups_hierarchy(keycloak_bootstrap):
    groups.create_group("testgroup", token=keycloak_bootstrap)
    groups.create_group("testgroup2", parent="testgroup", token=keycloak_bootstrap)
    ret = groups.list_groups(token=keycloak_bootstrap)
    assert list(ret.keys()) == ['testgroup','testgroup2']
    assert ret['testgroup']['children'] == ['testgroup2']

def test_create_group(keycloak_bootstrap):
    groups.create_group("testgroup", token=keycloak_bootstrap)

def test_create_subgroup(keycloak_bootstrap):
    groups.create_group("testgroup", token=keycloak_bootstrap)
    groups.create_group("testgroup2", parent="testgroup", token=keycloak_bootstrap)

def test_delete_group(keycloak_bootstrap):
    groups.create_group("testgroup", token=keycloak_bootstrap)
    groups.delete_group("testgroup", token=keycloak_bootstrap)
