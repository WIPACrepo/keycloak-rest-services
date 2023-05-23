import pytest

from ..util import keycloak_bootstrap
from krs import groups, users

from actions.deprovision_mailing_lists import process


@pytest.mark.asyncio
async def test_deprovision_mailing_lists(keycloak_bootstrap):
    await users.create_user('u1', first_name='first', last_name='last', email='email1@test',
                            rest_client=keycloak_bootstrap)
    await users.create_user('u2', first_name='first', last_name='last', email='email2@test',
                            rest_client=keycloak_bootstrap)

    await groups.create_group('/mailing-lists', rest_client=keycloak_bootstrap)
    await groups.create_group('/mailing-lists/ml', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/mailing-lists/ml', 'u1', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/mailing-lists/ml', 'u2', rest_client=keycloak_bootstrap)

    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/i', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/i/l', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/institutions/i/l', 'u1', rest_client=keycloak_bootstrap)

    await process('/mailing-lists', keycloak_bootstrap)
    ret = await groups.get_group_membership('/mailing-lists/ml', rest_client=keycloak_bootstrap)
    assert ret == ['u1']

