import pytest

from unittest.mock import MagicMock, call, patch

from ..util import keycloak_bootstrap  # type: ignore # noqa: F401
from krs.groups import create_group, add_user_group, delete_group, modify_group
from krs.users import create_user

from actions.sync_gws_calendars import sync_gws_calendars, ATTR_CAL_ID


# Data returned by the calendar ACL resource's list()
# noinspection SpellCheckingInspection
CALENDAR_ACL_LIST_RESPONSE = {
    'etag': '"p33genhe8obmoc0o"',
    'items': [
        # Not sure what this represents but all calendars have it
        {'etag': '"00000000000000000000"', 'kind': 'calendar#aclRule',
         'id': 'user:c_8@group.calendar.google.com',
         'role': 'owner', 'scope': {'type': 'user', 'value': 'c_8@group.calendar.google.com'}},
        # owner
        {'etag': '"00001718817190267000"', 'kind': 'calendar#aclRule',
         'id': 'user:owner@icecube.wisc.edu',
         'role': 'owner', 'scope': {'type': 'user', 'value': 'owner@icecube.wisc.edu'}},
        # writer
        {'etag': '"00001719001219334000"', 'kind': 'calendar#aclRule',
         'id': 'user:writer@icecube.wisc.edu',
         'role': 'writer', 'scope': {'type': 'user', 'value': 'writer@icecube.wisc.edu'}},
        # reader
        {'etag': '"00001719001219334000"', 'kind': 'calendar#aclRule',
         'id': 'user:reader@icecube.wisc.edu',
         'role': 'reader', 'scope': {'type': 'user', 'value': 'reader@icecube.wisc.edu'}},
        # group
        {'etag': '"00001719423647961000"', 'kind': 'calendar#aclRule',
            'id': 'group:group@icecube.wisc.edu',
            'role': 'reader', 'scope': {'type': 'group', 'value': 'group@icecube.wisc.edu'}},
        # domain
        {'etag': '"00001719423953352000"', 'kind': 'calendar#aclRule',
            'id': 'domain:icecube.wisc.edu',
            'role': 'reader', 'scope': {'type': 'domain', 'value': 'icecube.wisc.edu'}},
        # unexpected kind (not sure if it can be anything other than calendar#aclRule though)
        {'etag': '"00001719423647961000"', 'kind': 'NOT-AN-ACL-RULE',
         'id': 'user:not-an-acl-rule@icecube.wisc.edu',
         'role': 'reader', 'scope': {'type': 'user', 'value': 'not-an-acl-rule@icecube.wisc.edu'}},
    ],
    'kind': 'calendar#acl',
    'nextSyncToken': '00001719001219692000'}


def get_standard_mock_calendar_acl_client():
    mock_calendar_acl_request = MagicMock()
    mock_calendar_acl_request.execute = MagicMock(return_value=CALENDAR_ACL_LIST_RESPONSE)
    mock_calendar_acl_client = MagicMock()
    mock_calendar_acl_client.list = MagicMock(return_value=mock_calendar_acl_request)
    mock_calendar_acl_client.list_next = MagicMock(return_value=None)
    return mock_calendar_acl_client


async def setup_standard_keycloak_calendar(rest_client):
    await create_group('/calendars', rest_client=rest_client)
    await create_group('/calendars/cal', {ATTR_CAL_ID: 'calendar_id'}, rest_client=rest_client)
    await create_group('/calendars/cal/readers', rest_client=rest_client)
    await create_group('/calendars/cal/writers', rest_client=rest_client)

    await create_user("reader", "f", "l", "reader@test", rest_client=rest_client)
    await add_user_group("/calendars/cal/readers", "reader", rest_client=rest_client)

    await create_user("writer", "f", "l", "writer@test", rest_client=rest_client)
    await add_user_group("/calendars/cal/writers", "writer", rest_client=rest_client)


@pytest.mark.asyncio
async def test_sync_gws_calendars_no_changes(keycloak_bootstrap):  # noqa: F811
    await setup_standard_keycloak_calendar(keycloak_bootstrap)
    mock_calendar_acl_client = get_standard_mock_calendar_acl_client()
    service_account_creds = MagicMock()
    with patch("actions.sync_gws_calendars.build") as resource_builder:
        await sync_gws_calendars(calendar_acl=mock_calendar_acl_client,
                                 calendar_cals=MagicMock(),
                                 keycloak=keycloak_bootstrap,
                                 creds=service_account_creds,
                                 dryrun=False, notify=False)
        assert resource_builder.call_args_list == []
        assert service_account_creds.call_args_list == []
        assert mock_calendar_acl_client.delete.call_args_list == []
        assert mock_calendar_acl_client.insert.call_args_list == []
        assert mock_calendar_acl_client.patch.call_args_list == []


@pytest.mark.asyncio
async def test_sync_gws_calendars_ignore_owner(keycloak_bootstrap):  # noqa: F811
    await setup_standard_keycloak_calendar(keycloak_bootstrap)
    await create_user("owner", "f", "l", "owner@test", rest_client=keycloak_bootstrap)
    await add_user_group("/calendars/cal/writers", "owner", rest_client=keycloak_bootstrap)

    mock_calendar_acl_client = get_standard_mock_calendar_acl_client()
    service_account_creds = MagicMock()
    with patch("actions.sync_gws_calendars.build") as resource_builder:
        await sync_gws_calendars(calendar_acl=mock_calendar_acl_client,
                                 calendar_cals=MagicMock(),
                                 keycloak=keycloak_bootstrap,
                                 creds=service_account_creds,
                                 dryrun=False, notify=False)
        assert resource_builder.call_args_list == []
        assert service_account_creds.call_args_list == []
        assert mock_calendar_acl_client.delete.call_args_list == []
        assert mock_calendar_acl_client.insert.call_args_list == []
        assert mock_calendar_acl_client.patch.call_args_list == []


@pytest.mark.asyncio
async def test_sync_gws_calendars_delete(keycloak_bootstrap):  # noqa: F811
    await setup_standard_keycloak_calendar(keycloak_bootstrap)
    await delete_group("/calendars/cal/readers", rest_client=keycloak_bootstrap)
    mock_calendar_acl_client = get_standard_mock_calendar_acl_client()
    service_account_creds = MagicMock()
    with (patch("actions.sync_gws_calendars.build") as resource_builder):
        await sync_gws_calendars(calendar_acl=mock_calendar_acl_client,
                                 calendar_cals=MagicMock(),
                                 keycloak=keycloak_bootstrap,
                                 creds=service_account_creds,
                                 dryrun=False, notify=False)
        assert resource_builder.call_args_list == []
        assert service_account_creds.call_args_list == []
        assert mock_calendar_acl_client.delete.call_args_list == \
            [call(calendarId='calendar_id', ruleId='user:reader@icecube.wisc.edu')]
        assert mock_calendar_acl_client.insert.call_args_list == []
        assert mock_calendar_acl_client.patch.call_args_list == []


@pytest.mark.asyncio
async def test_sync_gws_calendars_insert(keycloak_bootstrap):  # noqa: F811
    await setup_standard_keycloak_calendar(keycloak_bootstrap)

    await create_user("new_reader", "f", "l", "new_eader@test", rest_client=keycloak_bootstrap)
    await add_user_group("/calendars/cal/readers", "new_reader", rest_client=keycloak_bootstrap)
    await create_user("new_writer", "f", "l", "new_writer@test", rest_client=keycloak_bootstrap)
    await add_user_group("/calendars/cal/writers", "new_writer", rest_client=keycloak_bootstrap)

    mock_calendar_acl_client = get_standard_mock_calendar_acl_client()
    service_account_creds = MagicMock()
    with (patch("actions.sync_gws_calendars.build") as resource_builder):
        await sync_gws_calendars(calendar_acl=mock_calendar_acl_client,
                                 calendar_cals=MagicMock(),
                                 keycloak=keycloak_bootstrap,
                                 creds=service_account_creds,
                                 dryrun=False, notify=False)
        assert resource_builder.call_args_list == \
            [call('calendar', 'v3', credentials=service_account_creds.with_subject(), cache_discovery=False),
             call('calendar', 'v3', credentials=service_account_creds.with_subject(), cache_discovery=False)]
        assert sorted(service_account_creds.with_subject.call_args_list) == \
            [call(), call(), call('new_reader@icecube.wisc.edu'), call('new_writer@icecube.wisc.edu')]
        expected_insert_calls = [
            call(calendarId='calendar_id',
                 body={'role': 'reader',
                       'scope': {'type': 'user', 'value': 'new_reader@icecube.wisc.edu'}}, sendNotifications=False),
            call(calendarId='calendar_id',
                 body={'role': 'writer',
                       'scope': {'type': 'user', 'value': 'new_writer@icecube.wisc.edu'}}, sendNotifications=False)]
        for call_ in mock_calendar_acl_client.insert.call_args_list:
            assert call_ in expected_insert_calls
        assert mock_calendar_acl_client.delete.call_args_list == []
        assert mock_calendar_acl_client.patch.call_args_list == []


@pytest.mark.asyncio
async def test_sync_gws_calendars_patch(keycloak_bootstrap):  # noqa: F811
    await setup_standard_keycloak_calendar(keycloak_bootstrap)
    # user reader becomes a writer
    await add_user_group("/calendars/cal/writers", "reader", rest_client=keycloak_bootstrap)
    mock_calendar_acl_client = get_standard_mock_calendar_acl_client()
    service_account_creds = MagicMock()
    with patch("actions.sync_gws_calendars.build") as resource_builder:
        await sync_gws_calendars(calendar_acl=mock_calendar_acl_client,
                                 calendar_cals=MagicMock(),
                                 keycloak=keycloak_bootstrap,
                                 creds=service_account_creds,
                                 dryrun=False, notify=False)
        assert resource_builder.call_args_list == []
        assert service_account_creds.call_args_list == []
        assert mock_calendar_acl_client.delete.call_args_list == []
        assert mock_calendar_acl_client.insert.call_args_list == []
        assert mock_calendar_acl_client.patch.call_args_list == [
            call(calendarId='calendar_id', ruleId='user:reader@icecube.wisc.edu',
                 body={'role': 'writer',
                       'scope': {'type': 'user', 'value': 'reader@icecube.wisc.edu'}})]


@pytest.mark.asyncio
async def test_sync_gws_calendars_delete_multiple(keycloak_bootstrap):  # noqa: F811
    await setup_standard_keycloak_calendar(keycloak_bootstrap)
    await modify_group('/calendars/cal', attrs={ATTR_CAL_ID: ['XXX', 'YYY']}, rest_client=keycloak_bootstrap)
    await delete_group("/calendars/cal/readers", rest_client=keycloak_bootstrap)
    mock_calendar_acl_client = get_standard_mock_calendar_acl_client()
    service_account_creds = MagicMock()
    with patch("actions.sync_gws_calendars.build") as resource_builder:
        await sync_gws_calendars(calendar_acl=mock_calendar_acl_client,
                                 calendar_cals=MagicMock(),
                                 keycloak=keycloak_bootstrap,
                                 creds=service_account_creds,
                                 dryrun=False, notify=False)
        assert resource_builder.call_args_list == []
        assert service_account_creds.call_args_list == []
        assert sorted(map(str, mock_calendar_acl_client.delete.call_args_list)) == \
               sorted(map(str, [call(calendarId='XXX', ruleId='user:reader@icecube.wisc.edu'),
                                call(calendarId='YYY', ruleId='user:reader@icecube.wisc.edu')]))
        assert mock_calendar_acl_client.insert.call_args_list == []
        assert mock_calendar_acl_client.patch.call_args_list == []
