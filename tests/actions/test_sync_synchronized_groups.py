import sys
from unittest.mock import MagicMock

import pytest

from krs.groups import (create_group, add_user_group, get_group_membership,
                        delete_group, group_info, modify_group)
from krs.institutions import create_inst, Region
from krs.users import create_user
# noinspection PyUnresolvedReferences
from ..util import keycloak_bootstrap  # type: ignore

import actions.sync_synchronized_groups as sync_synchronized_groups_module
from actions.sync_synchronized_groups import (auto_sync_enabled_groups, main, manual_group_sync,
                                              send_or_log_notification,
                                              SyncGroupNotificationConfig, SyncGroupConfig,
                                              MembershipSyncPolicy)
from attrs import fields


@pytest.mark.asyncio
async def test_sync_synchronized_group_authorlist(keycloak_bootstrap):
    await create_group('/mail', rest_client=keycloak_bootstrap)
    # noinspection PyTypeChecker,PyTestUnpassedFixture
    auto_sync_attr = fields(SyncGroupConfig).auto_sync.metadata['attr']
    # noinspection PyTypeChecker
    policy_attr = fields(SyncGroupConfig).policy.metadata['attr']
    # noinspection PyTypeChecker
    sources_expr_attr = fields(SyncGroupConfig).sources_expr.metadata['attr']
    # noinspection PyTypeChecker
    removal_grace_attr = fields(SyncGroupConfig).removal_grace_days.metadata['attr']
    # noinspection PyTypeChecker
    addition_occurred_notify_attr = fields(SyncGroupNotificationConfig).addition_occurred_notify.metadata['attr']
    # noinspection PyTypeChecker
    removal_pending_notify_attr = fields(SyncGroupNotificationConfig).removal_pending_notify.metadata['attr']
    # noinspection PyTypeChecker
    removal_averted_notify_attr = fields(SyncGroupNotificationConfig).removal_averted_notify.metadata['attr']
    # noinspection PyTypeChecker
    removal_occurred_notify_attr = fields(SyncGroupNotificationConfig).removal_occurred_notify.metadata['attr']
    # noinspection PyTypeChecker

    authorlist_expr = ("$..subGroups[?path == '/institutions/Experiment1']"
                       ".subGroups[?attributes.authorlist == 'true']"
                       ".subGroups[?name =~ '^authorlist.*'].path")
    default_attrs = {auto_sync_attr: "true",
                     policy_attr: MembershipSyncPolicy.match.value,
                     sources_expr_attr: authorlist_expr,
                     addition_occurred_notify_attr: "false",
                     removal_pending_notify_attr: "false",
                     removal_averted_notify_attr: "false",
                     removal_occurred_notify_attr: "false",
                     }

    g_authors = '/mail/authors'
    g_authors_grace = '/mail/authors-grace'
    g_authors_disabled = '/mail/authors-disabled'
    g_authors_prune = '/mail/authors-prune'
    all_synchronized_groups = [g_authors, g_authors_grace,
                               g_authors_disabled, g_authors_prune]

    await create_group(g_authors, rest_client=keycloak_bootstrap,
                       attrs=default_attrs)
    await create_group(g_authors_grace, rest_client=keycloak_bootstrap,
                       attrs=default_attrs | {removal_grace_attr: '1'})
    await create_group(g_authors_disabled, rest_client=keycloak_bootstrap,
                       attrs=default_attrs | {auto_sync_attr: 'false'})
    await create_group(g_authors_prune, rest_client=keycloak_bootstrap,
                       attrs=default_attrs | {policy_attr: MembershipSyncPolicy.prune.value})
    await create_group('/institutions', rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1', rest_client=keycloak_bootstrap)
    await create_group('/institutions/ExperimentXXX', rest_client=keycloak_bootstrap)

    # noinspection PyDictCreation
    inst_attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'A', 'is_US': False,
                  'region': Region.NORTH_AMERICA}

    # Note: authorlist subgroup created automatically

    inst_attrs['authorlist'] = 'true'
    await create_inst('Experiment1', 'Good', inst_attrs, rest_client=keycloak_bootstrap)
    await create_group('/institutions/Experiment1/Good/authorlist-special', rest_client=keycloak_bootstrap)

    inst_attrs['authorlist'] = 'false'
    await create_inst('Experiment1', 'Authorlist_false', inst_attrs, rest_client=keycloak_bootstrap)

    inst_attrs['authorlist'] = 'true'
    await create_inst('Experiment1', 'No_authorlist_subgroup', inst_attrs, rest_client=keycloak_bootstrap)
    await delete_group('/institutions/Experiment1/No_authorlist_subgroup/authorlist', rest_client=keycloak_bootstrap)

    inst_attrs['authorlist'] = 'true'
    await create_inst('ExperimentXXX', 'Irrelevant', inst_attrs, rest_client=keycloak_bootstrap)

    # pre-generate kwargs for create_user(), which requires unique emails, to keep things compact
    user_kwargs = [{'first_name': 'F', 'last_name': 'L', 'email': f'{i}@test', 'rest_client': keycloak_bootstrap}
                   for i in range(10)]

    u_add_to_authors = 'add-to-authors'
    await create_user(u_add_to_authors, **user_kwargs.pop())
    await add_user_group('/institutions/Experiment1/Good', u_add_to_authors, rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Good/authorlist-special', u_add_to_authors, rest_client=keycloak_bootstrap)  # noqa

    u_remain_in_authors = 'remain-in-authors'
    await create_user(u_remain_in_authors, **user_kwargs.pop())
    await add_user_group('/institutions/Experiment1/Good', u_remain_in_authors, rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Good/authorlist', u_remain_in_authors, rest_client=keycloak_bootstrap)  # noqa
    for group in all_synchronized_groups:
        await add_user_group(group, u_remain_in_authors, rest_client=keycloak_bootstrap)

    u_remove_bc_in_disabled = 'remove-in-disabled-authorlist'
    await create_user(u_remove_bc_in_disabled, **user_kwargs.pop())
    await add_user_group('/institutions/Experiment1/Authorlist_false', u_remove_bc_in_disabled, rest_client=keycloak_bootstrap)  # noqa
    await add_user_group('/institutions/Experiment1/Authorlist_false/authorlist', u_remove_bc_in_disabled, rest_client=keycloak_bootstrap)  # noqa
    for group in all_synchronized_groups:
        await add_user_group(group, u_remove_bc_in_disabled, rest_client=keycloak_bootstrap)

    u_dont_add_bc_wrong_expt = 'dont-add-wrong-experiment'
    await create_user(u_dont_add_bc_wrong_expt, **user_kwargs.pop())
    await add_user_group('/institutions/ExperimentXXX/Irrelevant', u_dont_add_bc_wrong_expt, rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/ExperimentXXX/Irrelevant/authorlist', u_dont_add_bc_wrong_expt, rest_client=keycloak_bootstrap)  # noqa

    await auto_sync_enabled_groups(keycloak_bootstrap, allow_notifications=False, dryrun=False)

    # noinspection PyTestUnpassedFixture
    async def get_deferred(group_path):
        grp = await group_info(group_path, rest_client=keycloak_bootstrap)
        cfg = SyncGroupConfig(group_path, grp['attributes'])
        return await cfg.get_deferred_removals(keycloak_bootstrap)

    authors_users = await get_group_membership(g_authors, rest_client=keycloak_bootstrap)
    assert set(authors_users) == {u_remain_in_authors, u_add_to_authors}
    assert not await get_deferred(g_authors)

    authors_disabled_users = await get_group_membership(g_authors_disabled, rest_client=keycloak_bootstrap)
    assert set(authors_disabled_users) == {u_remain_in_authors, u_remove_bc_in_disabled}
    assert not await get_deferred(g_authors_disabled)

    authors_prune_users = await get_group_membership(g_authors_prune, rest_client=keycloak_bootstrap)
    assert set(authors_prune_users) == {u_remain_in_authors}
    assert not await get_deferred(g_authors_prune)

    authors_grace_users = await get_group_membership(g_authors_grace, rest_client=keycloak_bootstrap)
    assert set(authors_grace_users) == {u_remain_in_authors, u_add_to_authors, u_remove_bc_in_disabled}
    authors_grace_deferred = await get_deferred(g_authors_grace)
    assert sorted(authors_grace_deferred.keys()) == [u_remove_bc_in_disabled]

    # simulate grace period expiration
    await modify_group(g_authors_grace, rest_client=keycloak_bootstrap,
                       attrs=default_attrs | {removal_grace_attr: '0'})
    await auto_sync_enabled_groups(keycloak_bootstrap, allow_notifications=False, dryrun=False)
    authors_grace_users2 = await get_group_membership(g_authors_grace, rest_client=keycloak_bootstrap)
    assert set(authors_grace_users2) == {u_remain_in_authors, u_add_to_authors}
    authors_grace_deferred = await get_deferred(g_authors_grace)
    assert not authors_grace_deferred.keys()

    # Sources expression produces non-string results
    with pytest.raises(TypeError):
        await manual_group_sync(g_authors_disabled, '$', keycloak_client=keycloak_bootstrap,
                                allow_notifications=False, dryrun=False)
    # Sources expression produces non-path results
    with pytest.raises(ValueError):
        await manual_group_sync(g_authors_disabled, '$..[*].name', keycloak_client=keycloak_bootstrap,
                                allow_notifications=False, dryrun=False)


@pytest.mark.asyncio
async def test_send_or_log_notification(monkeypatch):
    sent = []
    dummy_keycloak = MagicMock()

    async def fake_send_notification(username, subject, body, keycloak):
        sent.append((username, subject, body))

    monkeypatch.setattr(sync_synchronized_groups_module, 'send_notification', fake_send_notification)

    # notify=False: no-op, and a malformed template must not raise (lazy formatting)
    await send_or_log_notification(username='alice', subject='S', template='bad {unmatched',
                                   notify=False, dryrun=True, keycloak=dummy_keycloak)
    assert not sent

    # notify=True but template empty (event notification disabled): no-op
    await send_or_log_notification(username='alice', subject='S', template='',
                                   notify=True, dryrun=True, keycloak=dummy_keycloak)
    assert not sent

    # notify=True, dryrun=True: formats the message but only logs, does not send
    await send_or_log_notification(username='bob', subject='Removed',
                                   template='Hi {username}, group {group_path}',
                                   notify=True, dryrun=True, keycloak=dummy_keycloak, group_path='/mail/x')
    assert not sent

    # notify=True, dryrun=False: actually sends with the formatted body
    await send_or_log_notification(username='carol', subject='Removed',
                                   template='Hi {username}, group {group_path}',
                                   notify=True, dryrun=False, keycloak=dummy_keycloak, group_path='/mail/x')
    assert sent == [('carol', 'Removed', 'Hi carol, group /mail/x')]


def test_auto_allow_notifications_required_unless_dryrun(monkeypatch):
    monkeypatch.setattr(sync_synchronized_groups_module, 'get_rest_client', lambda: MagicMock())

    calls = []

    async def fake_auto_sync(**kwargs):
        calls.append(kwargs)
    monkeypatch.setattr(sync_synchronized_groups_module, 'auto_sync_enabled_groups', fake_auto_sync)

    # --auto without --allow-notifications and without --dryrun: blocked
    monkeypatch.setattr(sys, 'argv', ['prog', '--auto'])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    assert not calls

    # --auto --dryrun without --allow-notifications: allowed, notifications stay off
    monkeypatch.setattr(sys, 'argv', ['prog', '--auto', '--dryrun'])
    main()
    assert calls[-1]['allow_notifications'] is False

    # --auto --dryrun --allow-notifications: allowed, notifications on
    monkeypatch.setattr(sys, 'argv', ['prog', '--auto', '--dryrun', '--allow-notifications'])
    main()
    assert calls[-1]['allow_notifications'] is True

    # --auto --allow-notifications (no --dryrun): allowed
    monkeypatch.setattr(sys, 'argv', ['prog', '--auto', '--allow-notifications'])
    main()
    assert calls[-1]['allow_notifications'] is True
