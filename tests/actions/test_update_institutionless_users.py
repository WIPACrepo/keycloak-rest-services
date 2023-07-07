import pytest

from krs import users, groups, institutions
from ..util import keycloak_bootstrap

from actions.update_institutionless_users import update_institutionless_users


@pytest.mark.asyncio
async def test_update_institutionless_users(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'T', 'is_US': False,
             'region': institutions.Region.NORTH_AMERICA}
    await institutions.create_inst('IceCube', 'Test', attrs, rest_client=keycloak_bootstrap)

    await users.create_user('institutioned-no-changes', first_name='F', last_name='L', email='a@test',
                            attribs={'uidNumber':1000, 'gidNumber':1000}, rest_client=keycloak_bootstrap)
    await groups.add_user_group('/institutions/IceCube/Test', 'institutioned-no-changes', rest_client=keycloak_bootstrap)

    await users.create_user('institutionless-no-changes', first_name='F', last_name='L', email='b@test',
                            attribs={'uidNumber':1001, 'gidNumber':1001,
                                     'institutionless_since':'2023-07-07T13:07:56.400437'}, rest_client=keycloak_bootstrap)

    await users.create_user('make-institutioned', first_name='F', last_name='L', email='c@test',
                            attribs={'uidNumber':1002, 'gidNumber':1002,
                                     'institutionless_since':'2023-07-07T13:07:56.400437'}, rest_client=keycloak_bootstrap)
    await groups.add_user_group('/institutions/IceCube/Test', 'make-institutioned', rest_client=keycloak_bootstrap)

    await users.create_user('make-institutionless', first_name='F', last_name='L', email='d@test',
                            attribs={'uidNumber':1003, 'gidNumber':1003}, rest_client=keycloak_bootstrap)

    await update_institutionless_users(keycloak_client=keycloak_bootstrap)

    ret = await users.user_info('institutioned-no-changes', rest_client=keycloak_bootstrap)
    assert 'institutionless_since' not in ret['attributes']

    ret = await users.user_info('institutionless-no-changes', rest_client=keycloak_bootstrap)
    assert ret['attributes']['institutionless_since'] == '2023-07-07T13:07:56.400437'

    ret = await users.user_info('make-institutioned', rest_client=keycloak_bootstrap)
    assert 'institutionless_since' not in ret['attributes']

    ret = await users.user_info('make-institutionless', rest_client=keycloak_bootstrap)
    assert 'institutionless_since' in ret['attributes']
