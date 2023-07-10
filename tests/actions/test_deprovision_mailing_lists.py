import pytest
from datetime import datetime

from ..util import keycloak_bootstrap
from krs import groups, users

from actions.deprovision_mailing_lists import deprovision_mailing_lists


@pytest.mark.asyncio
async def test_deprovision_mailing_lists(keycloak_bootstrap):
    await groups.create_group('/insts', rest_client=keycloak_bootstrap)
    await groups.create_group('/insts/proj1', rest_client=keycloak_bootstrap)
    await groups.create_group('/insts/proj1/site', rest_client=keycloak_bootstrap)
    await groups.create_group('/insts/proj2', rest_client=keycloak_bootstrap)
    await groups.create_group('/insts/proj2/site', rest_client=keycloak_bootstrap)

    await groups.create_group('/ml', rest_client=keycloak_bootstrap)
    await groups.create_group('/ml/list', rest_client=keycloak_bootstrap)
    await groups.modify_group('/ml/list',
                              attrs={'allow_members_from_group_trees': ['/insts/proj1']},
                              rest_client=keycloak_bootstrap)

    await users.create_user('wrong-inst', first_name='first', last_name='last', email='emai0@test',
                            attribs={'uidNumber':999, 'gidNumber':999}, rest_client=keycloak_bootstrap)
    await groups.add_user_group('/ml/list', 'wrong-inst', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/insts/proj2/site', 'wrong-inst', rest_client=keycloak_bootstrap)

    await users.create_user('institutioned', first_name='first', last_name='last', email='email1@test',
                            attribs={'uidNumber':1000, 'gidNumber':1000}, rest_client=keycloak_bootstrap)
    await groups.add_user_group('/ml/list', 'institutioned', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/insts/proj1/site', 'institutioned', rest_client=keycloak_bootstrap)

    await users.create_user('institutionless-recent', first_name='first', last_name='last', email='email2@test',
                            attribs={'uidNumber':1001, 'gidNumber':1001,
                                     'institutionless_since':datetime.now().isoformat()},
                            rest_client=keycloak_bootstrap)
    await groups.add_user_group('/ml/list', 'institutionless-recent', rest_client=keycloak_bootstrap)

    await users.create_user('institutionless-old', first_name='first', last_name='last', email='email3@test',
                            attribs={'uidNumber':1002, 'gidNumber':1002,
                                     'institutionless_since':'2000-01-01T01:01:01.000001'},
                            rest_client=keycloak_bootstrap)
    await groups.add_user_group('/ml/list', 'institutionless-old', rest_client=keycloak_bootstrap)

    await deprovision_mailing_lists('/ml', 7, keycloak_bootstrap)
    ret = await groups.get_group_membership('/ml/list', rest_client=keycloak_bootstrap)
    assert set(ret) == {'institutioned', 'institutionless-recent'}
