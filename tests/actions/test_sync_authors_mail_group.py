import pytest

from krs.groups import create_group, add_user_group, get_group_membership
from krs.institutions import create_inst, Region
from krs.users import create_user
# noinspection PyUnresolvedReferences
from ..util import keycloak_bootstrap

from actions.sync_authors_mail_group import sync_authors_mail_group


@pytest.mark.asyncio
async def test_sync_authors_mail_group(keycloak_bootstrap):
    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/authors', rest_client=keycloak_bootstrap)

    await create_group('/institutions', rest_client=keycloak_bootstrap)
    await create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)

    # noinspection PyDictCreation
    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'A', 'is_US': False,
             'region': Region.NORTH_AMERICA}

    attrs['authorlist'] = 'true'
    await create_inst('IceCube', 'Good', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/IceCube/Good/authorlist', rest_client=keycloak_bootstrap)

    attrs['authorlist'] = 'false'
    await create_inst('IceCube', 'Authorlist_false', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/IceCube/Authorlist_false/authorlist', rest_client=keycloak_bootstrap)

    attrs['authorlist'] = 'true'
    await create_inst('IceCube', 'No_authorlist_subgroup', attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/IceCube/authorlist', rest_client=keycloak_bootstrap)

    # pre-generate kwargs for create_user(), which requires unique emails, to keep things compact
    user_kwargs = [{'first_name': 'F', 'last_name': 'L', 'email': f'{i}@test', 'rest_client': keycloak_bootstrap}
                   for i in range(10)]

    await create_user('add-to-authors', **user_kwargs.pop())
    await add_user_group('/institutions/IceCube/Good', 'add-to-authors', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/IceCube/Good/authorlist', 'add-to-authors', rest_client=keycloak_bootstrap)  # noqa

    await create_user('remain-in-authors', **user_kwargs.pop())
    await add_user_group('/mail/authors', 'remain-in-authors', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/IceCube/Good', 'remain-in-authors', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/IceCube/Good/authorlist', 'remain-in-authors', rest_client=keycloak_bootstrap)  # noqa

    await create_user('remove-in-disabled-authorlist', **user_kwargs.pop())
    await add_user_group('/mail/authors', 'remove-in-disabled-authorlist', rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/IceCube/Authorlist_false', 'remove-in-disabled-authorlist', rest_client=keycloak_bootstrap)  # noqa
    await add_user_group('/institutions/IceCube/Authorlist_false/authorlist', 'remove-in-disabled-authorlist', rest_client=keycloak_bootstrap)  # noqa

    await sync_authors_mail_group('/mail/authors', keycloak_client=keycloak_bootstrap)

    authors_users = await get_group_membership('/mail/authors', rest_client=keycloak_bootstrap)

    assert set(authors_users) == {'remain-in-authors', 'add-to-authors'}
