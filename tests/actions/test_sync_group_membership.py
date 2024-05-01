import pytest

from krs.groups import create_group, add_user_group, get_group_membership
from krs.institutions import create_inst, Region
from krs.users import create_user
# noinspection PyUnresolvedReferences
from ..util import keycloak_bootstrap  # type: ignore

from actions.sync_group_membership import sync_group_membership


@pytest.mark.asyncio
async def test_sync_group_membership(keycloak_bootstrap):
    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/authors', rest_client=keycloak_bootstrap)

    await create_group('/institutions', rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1', rest_client=keycloak_bootstrap)
    await create_group('/institutions/ExperimentXXX', rest_client=keycloak_bootstrap)

    # noinspection PyDictCreation
    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'A', 'is_US': False,
             'region': Region.NORTH_AMERICA}

    attrs['authorlist'] = 'true'
    await create_inst('Experiment1', 'Good', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1/Good/authorlist-special', rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1/Good/authorlist', rest_client=keycloak_bootstrap)

    attrs['authorlist'] = 'false'
    await create_inst('Experiment1', 'Authorlist_false', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1/Authorlist_false/authorlist', rest_client=keycloak_bootstrap)

    attrs['authorlist'] = 'true'
    await create_inst('Experiment1', 'No_authorlist_subgroup', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1/authorlist', rest_client=keycloak_bootstrap)

    attrs['authorlist'] = 'true'
    await create_inst('ExperimentXXX', 'Irrelevant', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/ExperimentXXX/Irrelevant/authorlist', rest_client=keycloak_bootstrap)

    # pre-generate kwargs for create_user(), which requires unique emails, to keep things compact
    user_kwargs = [{'first_name': 'F', 'last_name': 'L', 'email': f'{i}@test', 'rest_client': keycloak_bootstrap}
                   for i in range(10)]

    await create_user('add-to-authors', **user_kwargs.pop())
    await add_user_group('/institutions/Experiment1/Good', 'add-to-authors', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Good/authorlist-special', 'add-to-authors', rest_client=keycloak_bootstrap)  # noqa

    await create_user('remain-in-authors', **user_kwargs.pop())
    await add_user_group('/mail/authors', 'remain-in-authors', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Good', 'remain-in-authors', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Good/authorlist', 'remain-in-authors', rest_client=keycloak_bootstrap)  # noqa

    await create_user('remove-in-disabled-authorlist', **user_kwargs.pop())
    await add_user_group('/mail/authors', 'remove-in-disabled-authorlist', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Authorlist_false', 'remove-in-disabled-authorlist', rest_client=keycloak_bootstrap)  # noqa
    await add_user_group('/institutions/Experiment1/Authorlist_false/authorlist', 'remove-in-disabled-authorlist', rest_client=keycloak_bootstrap)  # noqa

    await create_user('wrong-experiment', **user_kwargs.pop())
    await add_user_group('/institutions/ExperimentXXX/Irrelevant', 'wrong-experiment', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/ExperimentXXX/Irrelevant/authorlist', 'wrong-experiment', rest_client=keycloak_bootstrap)  # noqa

    await sync_group_membership(
        [['/institutions', ''.join([
            '$.subGroups[?name == "Experiment1"]'
            '.subGroups[?attributes.authorlist == "true"]'
            '.subGroups[?name =~ "^authorlist.*"]'
            '.path'])]],
        '/mail/authors', keycloak_client=keycloak_bootstrap)

    authors_users = await get_group_membership('/mail/authors', rest_client=keycloak_bootstrap)

    assert set(authors_users) == {'remain-in-authors', 'add-to-authors'}
