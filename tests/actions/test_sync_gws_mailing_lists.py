import pytest

from unittest.mock import MagicMock, call

from ..util import keycloak_bootstrap  # noqa: F401
from krs.groups import create_group, modify_group, add_user_group
from krs.users import create_user

from actions.sync_gws_mailing_lists import sync_gws_mailing_lists


@pytest.mark.asyncio
async def test_sync_gws_mailing_lists_insert(keycloak_bootstrap):  # noqa: F811
    request_members = MagicMock()
    request_members.execute = MagicMock(
        return_value={'members': [
            {'email': 'keep.keep@icecube.wisc.edu', 'role': 'MEMBER'},
            {'email': 'owner@test', 'role': 'OWNER'}]})
    gws_members_client = MagicMock()
    gws_members_client.list = MagicMock(return_value=request_members)
    gws_members_client.list_next = MagicMock(return_value=None)

    request_groups = MagicMock()
    request_groups.execute = MagicMock(
        return_value={'groups': [{'email': 'test@gws'}]})
    gws_groups_client = MagicMock()
    gws_groups_client.list = MagicMock(return_value=request_groups)

    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/list', rest_client=keycloak_bootstrap)
    await modify_group('/mail/list', attrs={'email': ['test@gws']}, rest_client=keycloak_bootstrap)

    await create_user('keep', first_name='keep', last_name='keep', email='keep@test', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'keep', rest_client=keycloak_bootstrap)

    await create_user('add', first_name='add', last_name='add', email='add@test', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'add', rest_client=keycloak_bootstrap)

    await sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_bootstrap, dryrun=False)

    assert gws_members_client.insert.call_args_list == \
           [call(groupKey='test@gws', body={'email': 'add.add@icecube.wisc.edu',
                                            'role': 'MEMBER'})]
    assert gws_members_client.delete.call_count == 0
    assert gws_members_client.patch.call_count == 0


@pytest.mark.asyncio
async def test_sync_gws_mailing_lists_delete(keycloak_bootstrap):  # noqa: F811
    request_members = MagicMock()
    request_members.execute = MagicMock(
        return_value={'members': [
            {'email': 'keep.keep@icecube.wisc.edu', 'role': 'MEMBER'},
            {'email': 'owner@test', 'role': 'OWNER'},
            {'email': 'remove@test', 'role': 'MEMBER'}]})
    gws_members_client = MagicMock()
    gws_members_client.list = MagicMock(return_value=request_members)
    gws_members_client.list_next = MagicMock(return_value=None)

    request_groups = MagicMock()
    request_groups.execute = MagicMock(
        return_value={'groups': [{'email': 'test@gws'}]})
    gws_groups_client = MagicMock()
    gws_groups_client.list = MagicMock(return_value=request_groups)

    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/list', rest_client=keycloak_bootstrap)
    await modify_group('/mail/list', attrs={'email': ['test@gws']}, rest_client=keycloak_bootstrap)

    await create_user('keep', first_name='keep', last_name='keep', email='keep@test', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'keep', rest_client=keycloak_bootstrap)

    await sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_bootstrap, dryrun=False)

    assert gws_members_client.delete.call_args_list == \
        [call(groupKey='test@gws', memberKey='remove@test')]
    assert gws_members_client.insert.call_count == 0
    assert gws_members_client.patch.call_count == 0


@pytest.mark.asyncio
async def test_sync_gws_mailing_lists_patch(keycloak_bootstrap):  # noqa: F811
    request_members = MagicMock()
    request_members.execute.side_effect = [
        {'members': [{'email': 'change.role@icecube.wisc.edu', 'role': 'MEMBER'}]},
        {'members': [{'email': 'change.role@icecube.wisc.edu', 'role': 'MANAGER'}]}]
    gws_members_client = MagicMock()
    gws_members_client.list = MagicMock(return_value=request_members)
    gws_members_client.list_next = MagicMock(return_value=None)

    request_groups = MagicMock()
    request_groups.execute = MagicMock(
        return_value={'groups': [{'email': 'test@gws'}]})
    gws_groups_client = MagicMock()
    gws_groups_client.list = MagicMock(return_value=request_groups)

    await create_group('/mail', rest_client=keycloak_bootstrap)
    await create_group('/mail/list', rest_client=keycloak_bootstrap)
    await modify_group('/mail/list', attrs={'email': ['test@gws']}, rest_client=keycloak_bootstrap)
    await create_group('/mail/list/_admin', rest_client=keycloak_bootstrap)

    await create_user('change-role', first_name='change', last_name='role', email='c-r@test', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list', 'change-role', rest_client=keycloak_bootstrap)
    await add_user_group('/mail/list/_admin', 'change-role', rest_client=keycloak_bootstrap)

    await sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_bootstrap, dryrun=False)

    assert gws_members_client.patch.call_args_list == \
        [call(groupKey='test@gws', memberKey='change.role@icecube.wisc.edu',
              body={'email': 'change.role@icecube.wisc.edu', 'role': 'MANAGER'})]
    assert gws_members_client.insert.call_count == 0
    assert gws_members_client.delete.call_count == 0
