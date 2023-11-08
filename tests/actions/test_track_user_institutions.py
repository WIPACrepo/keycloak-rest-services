import pytest
from datetime import datetime

from krs import users, groups, institutions
# noinspection PyUnresolvedReferences
from ..util import keycloak_bootstrap

from actions.track_user_institutions import update_institution_tracking


@pytest.mark.asyncio
async def test_update_institutionless_users(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'T', 'is_US': False,
             'region': institutions.Region.NORTH_AMERICA}

    await institutions.create_inst('IceCube', 'A', attrs, rest_client=keycloak_bootstrap)
    await institutions.create_inst('IceCube', 'B', attrs, rest_client=keycloak_bootstrap)

    kwargs = {'first_name': 'F', 'last_name': 'L', 'email': 'a@test',
              'attribs': {"institutions_last_seen": "/institutions/IceCube/A",
                          "institutions_last_changed": '2023-07-07T13:07:56.400437'},
              'rest_client': keycloak_bootstrap}
    await users.create_user('no-changes1', **kwargs)
    await groups.add_user_group('/institutions/IceCube/A', 'no-changes1', rest_client=keycloak_bootstrap)

    kwargs = {'first_name': 'F', 'last_name': 'L', 'email': 'b@test',
              'attribs': {"institutions_last_seen": "/institutions/IceCube/A,/institutions/IceCube/B",
                          "institutions_last_changed": '2023-07-07T13:07:56.400437'},
              'rest_client': keycloak_bootstrap}
    await users.create_user('no-changes2', **kwargs)
    await groups.add_user_group('/institutions/IceCube/A', 'no-changes2', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/institutions/IceCube/B', 'no-changes2', rest_client=keycloak_bootstrap)

    kwargs = {'first_name': 'F', 'last_name': 'L', 'email': 'c@test',
              'attribs': {"institutions_last_seen": "/institutions/IceCube/A,/institutions/IceCube/B",
                          "institutions_last_changed": '2023-07-07T13:07:56.400437'},
              'rest_client': keycloak_bootstrap}
    await users.create_user('remove-b', **kwargs)
    await groups.add_user_group('/institutions/IceCube/A', 'remove-b', rest_client=keycloak_bootstrap)

    kwargs = {'first_name': 'F', 'last_name': 'L', 'email': 'd@test',
              'attribs': {"institutions_last_seen": "/institutions/IceCube/A",
                          "institutions_last_changed": '2023-07-07T13:07:56.400437'},
              'rest_client': keycloak_bootstrap}
    await users.create_user('remove-all', **kwargs)

    kwargs = {'first_name': 'F', 'last_name': 'L', 'email': 'e@test',
              'attribs': {},
              'rest_client': keycloak_bootstrap}
    await users.create_user('new-add-ab', **kwargs)
    await groups.add_user_group('/institutions/IceCube/A', 'new-add-ab', rest_client=keycloak_bootstrap)
    await groups.add_user_group('/institutions/IceCube/B', 'new-add-ab', rest_client=keycloak_bootstrap)

    kwargs = {'first_name': 'F', 'last_name': 'L', 'email': 'f@test',
              'attribs': {"institutions_last_seen": "none",
                          "institutions_last_changed": '2023-07-07T13:07:56.400437'},
              'rest_client': keycloak_bootstrap}
    await users.create_user('no-inst-add-a', **kwargs)
    await groups.add_user_group('/institutions/IceCube/A', 'no-inst-add-a', rest_client=keycloak_bootstrap)

    await update_institution_tracking(keycloak_client=keycloak_bootstrap, notify=False, dryrun=False)

    all_users = await users.list_users(rest_client=keycloak_bootstrap)

    assert all_users['no-changes1']['attributes']["institutions_last_seen"] == \
           "/institutions/IceCube/A"
    assert all_users['no-changes2']['attributes']["institutions_last_seen"] == \
           "/institutions/IceCube/A,/institutions/IceCube/B"
    assert all_users['remove-b']['attributes']["institutions_last_seen"] == \
           "/institutions/IceCube/A"
    assert all_users['remove-all']['attributes']["institutions_last_seen"] == 'none'
    assert all_users['new-add-ab']['attributes']["institutions_last_seen"] == \
           "/institutions/IceCube/A,/institutions/IceCube/B"
    assert datetime.fromisoformat(
        all_users['new-add-ab']['attributes']["institutions_last_changed"])
    assert all_users['no-inst-add-a']['attributes']["institutions_last_seen"] == \
           "/institutions/IceCube/A"
