import pytest

from unittest.mock import MagicMock, call, patch, Mock

from ..util import keycloak_bootstrap  # type: ignore # noqa: F401
from krs.groups import create_group, add_user_group
from krs.users import create_user, modify_user

from actions.sync_gws_calendars import sync_gws_calendars, foo, ATTR_CAL_ID


# class MockCalendar:
#     def __init__(self, *args, **kwargs):
#         self._acl = MagicMock()
#
#     def acl(self):
#         return self._acl
#
#
# MOCK_CALENDAR = MockCalendar()
#
#
# def _build(*args, **kwargs):
#     return MagicMock()
#
#
# @pytest.fixture(autouse=True, scope="function")
# def mock_build():
#     with patch("actions.sync_gws_calendars.build", new=_build) as build:
#         yield build
#
#
# def _retry(request, max_attempts):
#     return
#
#
# @pytest.fixture(autouse=True, scope="function")
# def mock_get_gws_cal_user_acl_rules():
#     with patch("actions.util.retry_execute") as retry:
#         yield retry
#     yield None


# noinspection SpellCheckingInspection
CAL_ALC_RESP = \
    {'etag': '"p33genhe8obmoc0o"',
     'items': [{'etag': '"00000000000000000000"',
                'id': 'user:c_8f80ce209d89e843f9c01ff6e57543e03d7e5ef8f06d00d453aed0b8eabcf943@group.calendar.google.com',
                'kind': 'calendar#aclRule',
                'role': 'owner',
                'scope': {'type': 'user',
                          'value': 'c_8f80ce209d89e843f9c01ff6e57543e03d7e5ef8f06d00d453aed0b8eabcf943@group.calendar.google.com'}},
               {'etag': '"00001718817190267000"',
                'id': 'user:vbrik_gadm@icecube.wisc.edu',
                'kind': 'calendar#aclRule',
                'role': 'owner',
                'scope': {'type': 'user', 'value': 'vbrik_gadm@icecube.wisc.edu'}},
               {'etag': '"00001719001219334000"',
                'id': 'user:vbrik@icecube.wisc.edu',
                'kind': 'calendar#aclRule',
                'role': 'writer',
                'scope': {'type': 'user', 'value': 'vbrik@icecube.wisc.edu'}}],
     'kind': 'calendar#acl',
     'nextSyncToken': '00001719001219692000'}


@pytest.mark.asyncio
async def test_sync_gws_calendars_remove(keycloak_bootstrap):  # noqa: F811
    mock_calendar_acl_request = MagicMock()
    mock_calendar_acl_request.execute = MagicMock(return_value=CAL_ALC_RESP)
    mock_calendar_acl_client = MagicMock()
    mock_calendar_acl_client.list = MagicMock(return_value=mock_calendar_acl_request)
    mock_calendar_acl_client.list_next = MagicMock(return_value=None)

    await create_group('/calendars', rest_client=keycloak_bootstrap)
    await create_group('/calendars/cal', {ATTR_CAL_ID: 'id'}, rest_client=keycloak_bootstrap)
    await create_group('/calendars/cal/readers', rest_client=keycloak_bootstrap)
    await create_group('/calendars/cal/writers', rest_client=keycloak_bootstrap)

    await create_user("add", "f", "l", "add@test", rest_client=keycloak_bootstrap)
    await add_user_group("/calendars/cal/readers", "add", rest_client=keycloak_bootstrap)

    with patch("actions.sync_gws_calendars.build") as build:
        await sync_gws_calendars(mock_calendar_acl_client, keycloak_bootstrap, MagicMock(), False, False)
        print(build)
        assert False
        
#     request_list_members = MagicMock()
#     request_list_members.execute = MagicMock(
#         return_value={'members': [
#             {'email': 'keep.keep@icecube.wisc.edu', 'role': 'MEMBER'},
#             {'email': 'keep.subgroup@icecube.wisc.edu', 'role': 'MEMBER'},
#             {'email': 'owner-dont-delete@test', 'role': 'OWNER'}]})
#     gws_members_client = MagicMock()
#     gws_members_client.list = MagicMock(return_value=request_list_members)
#     gws_members_client.list_next = MagicMock(return_value=None)
#
#     request_groups = MagicMock()
#     request_groups.execute = MagicMock(
#         return_value={'groups': [{'email': 'test@gws'}]})
#     gws_groups_client = MagicMock()
#     gws_groups_client.list = MagicMock(return_value=request_groups)
#
#     await create_group('/mail', rest_client=keycloak_bootstrap)
#     await create_group('/mail/list', attrs={'email': 'test@gws'}, rest_client=keycloak_bootstrap)
#     await create_group('/mail/list/_admin', rest_client=keycloak_bootstrap)
#     await create_group('/mail/list/subgroup', rest_client=keycloak_bootstrap)
#     await create_group('/mail/list/subgroup/_managers', rest_client=keycloak_bootstrap)
#
#     _setup_user = partial(setup_user, rest_client=keycloak_bootstrap)
#
#     await _setup_user('keep', 'keep', ['/mail/list'])
#     await _setup_user('add', 'add', ['/mail/list'])
#     await _setup_user('add', 'custom', ['/mail/list'], {'mailing_list_email': 'custom@ext'})
#     await _setup_user('add', 'manager', ['/mail/list/_admin'])
#     await _setup_user('add', 'subgroup', ['/mail/list/subgroup'])
#     await _setup_user('keep', 'subgroup', ['/mail/list/subgroup'])
#     await _setup_user('add', 'sub-mgr', ['/mail/list/subgroup/_managers'])
#
#     await sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_bootstrap,
#                                  send_notifications=False, dryrun=False)
#
#     assert (sorted(map(repr, gws_members_client.insert.call_args_list)) ==
#             sorted(map(repr, [
#                 call(groupKey='test@gws', body={'email': 'add.add@icecube.wisc.edu',
#                                                 'delivery_settings': 'ALL_MAIL',
#                                                 'role': 'MEMBER'}),
#                 call(groupKey='test@gws', body={'email': 'custom@ext',
#                                                 'delivery_settings': 'ALL_MAIL',
#                                                 'role': 'MEMBER'}),
#                 call(groupKey='test@gws', body={'email': 'add.custom@icecube.wisc.edu',
#                                                 'delivery_settings': 'NONE',
#                                                 'role': 'MEMBER'}),
#                 call(groupKey='test@gws', body={'email': 'add.subgroup@icecube.wisc.edu',
#                                                 'delivery_settings': 'ALL_MAIL',
#                                                 'role': 'MEMBER'}),
#                 call(groupKey='test@gws', body={'email': 'add.manager@icecube.wisc.edu',
#                                                 'delivery_settings': 'ALL_MAIL',
#                                                 'role': 'MANAGER'}),
#                 call(groupKey='test@gws', body={'email': 'add.sub-mgr@icecube.wisc.edu',
#                                                 'delivery_settings': 'ALL_MAIL',
#                                                 'role': 'MANAGER'}),
#             ])))
#     assert gws_members_client.delete.call_args_list == []
#     assert gws_members_client.patch.call_args_list == []
#
#
# @pytest.mark.asyncio
# async def test_sync_gws_mailing_lists_delete(keycloak_bootstrap):  # noqa: F811
#     request_members = MagicMock()
#     request_members.execute = MagicMock(
#         return_value={'members': [
#             {'email': 'keep.keep@icecube.wisc.edu', 'role': 'MEMBER'},
#             {'email': 'keep.sub@icecube.wisc.edu', 'role': 'MEMBER'},
#             {'email': 'owner-dont-delete@test', 'role': 'OWNER'},
#             {'email': 'keep.subadmin@icecube.wisc.edu', 'role': 'MANAGER'},
#             {'email': 'remove@test', 'role': 'MEMBER'},
#         ]})
#     gws_members_client = MagicMock()
#     gws_members_client.list = MagicMock(return_value=request_members)
#     gws_members_client.list_next = MagicMock(return_value=None)
#
#     request_groups = MagicMock()
#     request_groups.execute = MagicMock(
#         return_value={'groups': [{'email': 'test@gws'}]})
#     gws_groups_client = MagicMock()
#     gws_groups_client.list = MagicMock(return_value=request_groups)
#
#     await create_group('/mail', rest_client=keycloak_bootstrap)
#     await create_group('/mail/list', attrs={'email': 'test@gws'}, rest_client=keycloak_bootstrap)
#     await create_group('/mail/list/sub', rest_client=keycloak_bootstrap)
#     await create_group('/mail/list/sub/_admin', rest_client=keycloak_bootstrap)
#
#     await setup_user('keep', 'keep', ['/mail/list'], rest_client=keycloak_bootstrap)
#     await setup_user('keep', 'sub', ['/mail/list/sub'], rest_client=keycloak_bootstrap)
#     await setup_user('keep', 'subadmin', ['/mail/list/sub/_admin'], rest_client=keycloak_bootstrap)
#
#     await sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_bootstrap,
#                                  send_notifications=False, dryrun=False)
#
#     assert (sorted(map(repr, gws_members_client.delete.call_args_list)) ==
#             sorted(map(repr, [
#                 call(groupKey='test@gws', memberKey='remove@test'),
#             ])))
#     assert gws_members_client.insert.call_args_list == []
#     assert gws_members_client.patch.call_args_list == []
#
#
# @pytest.mark.asyncio
# async def test_sync_gws_mailing_lists_patch(keycloak_bootstrap):  # noqa: F811
#     request_members = MagicMock()
#     request_members.execute.side_effect = [
#         {'members': [
#             {'email': 'make.manager@icecube.wisc.edu', 'role': 'MEMBER'},
#             {'email': 'make.member@icecube.wisc.edu', 'role': 'MANAGER'},
#         ]},
#     ]
#     gws_members_client = MagicMock()
#     gws_members_client.list = MagicMock(return_value=request_members)
#     gws_members_client.list_next = MagicMock(return_value=None)
#
#     request_groups = MagicMock()
#     request_groups.execute = MagicMock(
#         return_value={'groups': [{'email': 'test@gws'}]})
#     gws_groups_client = MagicMock()
#     gws_groups_client.list = MagicMock(return_value=request_groups)
#
#     await create_group('/mail', rest_client=keycloak_bootstrap)
#     await create_group('/mail/list', attrs={'email': 'test@gws'}, rest_client=keycloak_bootstrap)
#     await create_group('/mail/list/_admin', rest_client=keycloak_bootstrap)
#
#     await setup_user('make', 'manager', ['/mail/list', '/mail/list/_admin'], rest_client=keycloak_bootstrap)
#     await setup_user('make', 'member', ['/mail/list'], rest_client=keycloak_bootstrap)
#
#     await sync_gws_mailing_lists(gws_members_client, gws_groups_client, keycloak_bootstrap,
#                                  send_notifications=False, dryrun=False)
#
#     assert (sorted(map(repr, gws_members_client.patch.call_args_list)) ==
#             sorted(map(repr, [
#                 call(groupKey='test@gws', memberKey='make.manager@icecube.wisc.edu',
#                      body={'email': 'make.manager@icecube.wisc.edu', 'role': 'MANAGER'}),
#                 call(groupKey='test@gws', memberKey='make.member@icecube.wisc.edu',
#                      body={'email': 'make.member@icecube.wisc.edu', 'role': 'MEMBER'}),
#             ])))
#     assert gws_members_client.insert.call_args_list == []
#     assert gws_members_client.delete.call_args_list == []
