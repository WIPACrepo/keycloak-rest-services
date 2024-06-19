#!/usr/bin/env python
import argparse
import asyncio
import logging
import sys
from pprint import pprint

from contextlib import suppress
from google.oauth2 import service_account
from googleapiclient.discovery import build

from rest_tools.client import RestClient

from krs.token import get_rest_client
from krs.groups import get_group_membership, group_info, list_groups, GroupDoesNotExist
from krs.users import user_info, UserDoesNotExist
from krs.email import send_email

from actions.util import retry_execute, group_tree_to_list, reflow_text

from attrs import define, field, fields, NOTHING


ACTION_ID = 'sync_gws_calendars'


def get_gws_cal_user_acl_rules(calendar_id, gws_admin_creds):
    cal = build('calendar', 'v3', credentials=gws_admin_creds)
    cal_acl_res = cal.acl()

    acl_rules = {}
    request = cal_acl_res.list(calendarId=calendar_id)
    while request is not None:
        response = retry_execute(request)
        for item in response.get('items', []):
            if (item['kind'] != 'calendar#aclRule'
                    or item['id'].endswith('@group.calendar.google.com')
                    or item['scope']['type'] != 'user'):
                continue
            addr = item['scope']['value']
            acl_rules[addr]['role'] = item['role']
            acl_rules[addr]['scope'] = item['scope']
            acl_rules[addr]['id'] = item['id']
        request = cal_acl_res.list_next(request, response)
    return acl_rules


async def get_kc_user_acl_rules(group, role, keycloak):
    try:
        role_usernames = await get_group_membership(f"{group['path']}/{role}", rest_client=keycloak)
    except GroupDoesNotExist:
        role_usernames = []
    acl_rules = {}
    for username in role_usernames:
        acl_rules[username]['role'] = role
        acl_rules[username]['scope'] = {'type': 'user', 'value': f'{username}@icecube.wisc.edu'}
    return acl_rules


async def sync_gws_calendars(gws_admin_creds, keycloak):
    all_groups = await list_groups(rest_client=keycloak)
    cal_groups = [g for g in (await group_info('/calendars'))['subGroups']
                  if 'calendar_id' in g['attributes']]

    for cal_group in cal_groups:
        if not (cal_id := cal_group.get('attributes', {}).get('calendar_id')):
            continue
        kc_writer_rules = await get_kc_user_acl_rules(cal_group, "writer", keycloak)
        kc_reader_rules = await get_kc_user_acl_rules(cal_group, "reader", keycloak)
        target_rules = kc_reader_rules | kc_writer_rules

        actual_acl_rules = get_gws_cal_user_acl_rules(cal_id, gws_admin_creds)
        owners = set(addr for addr, rule in actual_acl_rules.items() if rule["role"] == "owner")

        acl_res = build('calendar', 'v3', credentials=gws_admin_creds).acl
        for addr in set(actual_acl_rules) - set(target_rules):
            if addr in owners:
                continue
            req = acl_res.delete(calendarId=cal_id, ruleId=actual_acl_rules[addr]['id'])
            retry_execute(req)

        for addr in target_rules:
            if addr in owners:
                continue
            if addr in actual_acl_rules:
                if actual_acl_rules[addr]['role'] != target_rules[addr]['role']:
                    req = acl_res.patch(calendarId=cal_id, ruleId=actual_acl_rules[addr]['id'],
                                        body={target_rules[addr]})
                    retry_execute(req)
                continue

            req = acl_res.insert(calendarId=cal_id, body=target_rules[addr])
            retry_execute(req)
            user_creds = gws_admin_creds.with_subject(addr)
            user_cal_list = build('calendar', 'v3', credentials=user_creds).calendarList()
            req = user_cal_list.insert(body={'id': cal_id, 'selected': True})
            retry_execute(req)












def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='XXX',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='XXX')
    parser.add_argument('--sa-credentials', metavar='PATH', required=True,
                        help='JSON file with service account credentials')
    parser.add_argument('--sa-subject', metavar='EMAIL', required=True,
                        help='principal on whose behalf the service account will act')
    parser.add_argument('--log-level', default='info', choices=('debug', 'info', 'warning', 'error'),
                        help='Root logger level.')
    parser.add_argument('--log-level-this', default='info', choices=('debug', 'info', 'warning', 'error'),
                        help='Logging level of this application (not dependencies).')
    parser.add_argument('--log-level-client', default='warning', choices=('debug', 'info', 'warning', 'error'),
                        help='REST client logging level.')
    parser.add_argument('--dryrun', action='store_true', help='dry run')
    args = vars(parser.parse_args())

    logging.basicConfig(level=getattr(logging, args['log_level'].upper()))
    cca_logger = logging.getLogger('ClientCredentialsAuth')
    cca_logger.setLevel(getattr(logging, args['log_level_client'].upper()))
    this_logger = logging.getLogger(ACTION_ID)
    this_logger.setLevel(getattr(logging, args['log_level_this'].upper()))

    keycloak_client = get_rest_client()

    creds = service_account.Credentials.from_service_account_file(
        args['sa_credentials'], subject=args['sa_subject'],
        scopes=['https://www.googleapis.com/auth/admin.directory.user',
                'https://www.googleapis.com/auth/admin.directory.resource.calendar',
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.events',
                'https://www.googleapis.com/auth/admin.directory.resource.calendar',
                'https://www.googleapis.com/auth/admin.directory.resource.calendar.readonly',
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.events',
                'https://www.googleapis.com/auth/calendar.events.readonly',
                'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/calendar.settings.readonly'])

    asyncio.run(sync_gws_calendars(creds, keycloak_client))

if __name__ == '__main__':
    sys.exit(main())

