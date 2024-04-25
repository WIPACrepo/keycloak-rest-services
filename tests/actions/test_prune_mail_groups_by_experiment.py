import pytest
from datetime import datetime

from ..util import keycloak_bootstrap
from krs.groups import create_group, modify_group, add_user_group, get_group_membership
from krs.users import create_user
from krs.institutions import create_inst, Region

from actions.prune_mail_groups_by_experiment import prune_mail_groups


@pytest.mark.asyncio
async def test_prune_mail_groups(keycloak_bootstrap):
    await create_group('/institutions', rest_client=keycloak_bootstrap)
    await create_group('/institutions/foo', rest_client=keycloak_bootstrap)
    await create_group('/institutions/bar', rest_client=keycloak_bootstrap)

    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'T', 'is_US': False,
             'region': Region.NORTH_AMERICA}
    await create_inst('foo', 'A', attrs, rest_client=keycloak_bootstrap)
    await create_inst('bar', 'B', attrs, rest_client=keycloak_bootstrap)

    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/list', rest_client=keycloak_bootstrap)
    await modify_group('/mail/list',
                       attrs={'allow_members_from_experiments': ['foo']},
                       rest_client=keycloak_bootstrap)
    await create_group('/mail/list/subgroup', rest_client=keycloak_bootstrap)

    await create_user('good', first_name='first', last_name='last', email='z@test',
                      attribs={"institutions_last_seen": "/institutions/foo/A",
                               "institutions_last_changed": '2001-01-01T01:01:01.000001'},
                      rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'good', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list/subgroup', 'good', rest_client=keycloak_bootstrap)

    await create_user('wrong-exp', first_name='first', last_name='last', email='a@test',
                      attribs={"institutions_last_seen": "/institutions/bar/B",
                               "institutions_last_changed": '2001-01-01T01:01:01.000001'},
                      rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'wrong-exp', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list/subgroup', 'wrong-exp', rest_client=keycloak_bootstrap)

    await create_user('wrong-exp-grace', first_name='first', last_name='last', email='b@test',
                      attribs={"institutions_last_seen": "/institutions/bar/B",
                               "institutions_last_changed": datetime.now().isoformat()},
                      rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'wrong-exp-grace', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list/subgroup', 'wrong-exp-grace', rest_client=keycloak_bootstrap)

    await create_user('homeless', first_name='first', last_name='last', email='c@test',
                      attribs={},
                      rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'homeless', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list/subgroup', 'homeless', rest_client=keycloak_bootstrap)

    await prune_mail_groups(7, None, False, keycloak_bootstrap)

    ret = await get_group_membership('/mail/list', rest_client=keycloak_bootstrap)
    assert set(ret) == {'good', 'wrong-exp-grace'}

    ret = await get_group_membership('/mail/list/subgroup', rest_client=keycloak_bootstrap)
    assert set(ret) == {'good', 'wrong-exp-grace'}
