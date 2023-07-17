import pytest

from unittest.mock import MagicMock

from ..util import keycloak_bootstrap  # noqa: F401
from krs.groups import create_group, modify_group, add_user_group
from krs.users import create_user

from actions.sync_gws_mailing_lists import sync_gws_mailing_lists


@pytest.mark.asyncio
async def test_sync_gws_mailing_lists(keycloak_bootstrap):  # noqa: F811
    request = MagicMock()
    request.execute = MagicMock(
        return_value={'members': [{'email': 'keep.keep@icecube.wisc.edu'},
                                  {'email': 'remove@test'}]})
    gws_members_client = MagicMock()
    gws_members_client.list = MagicMock(return_value=request)
    gws_members_client.list_next = MagicMock(return_value=None)
    gws_members_client.insert = MagicMock()
    gws_members_client.delete = MagicMock()

    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/list', rest_client=keycloak_bootstrap)
    await modify_group('/mail/list', attrs={'email': ['test@gws']}, rest_client=keycloak_bootstrap)

    await create_user('keep', first_name='keep', last_name='keep', email='keep@test', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'keep', rest_client=keycloak_bootstrap)

    await create_user('add', first_name='add', last_name='add', email='add@test', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'add', rest_client=keycloak_bootstrap)

    ret = await sync_gws_mailing_lists(gws_members_client, keycloak_bootstrap, dryrun=False)

    gws_members_client.list.assert_called_once()
    gws_members_client.list_next.assert_called_once()
    gws_members_client.insert.assert_called_once()
    gws_members_client.delete.assert_called_once()
    request.execute.assert_called_once()

    assert ret == {"added": {"add.add@icecube.wisc.edu"}, "deleted": {"remove@test"}}
