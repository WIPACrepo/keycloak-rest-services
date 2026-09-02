import sys
from unittest.mock import MagicMock

import pytest
from attrs import fields

import actions.sync_synchronized_groups as sync_synchronized_groups_module
from actions.sync_synchronized_groups import (
    MembershipSyncPolicy,
    SyncGroupConfig,
    SyncGroupNotificationConfig,
    auto_sync_enabled_groups,
    get_group_membership_cached,
    group_id_by_path,
    main,
    manual_group_sync,
    send_or_log_notification,
)
from krs.groups import (
    GroupDoesNotExist,
    add_user_group,
    create_group,
    delete_group,
    get_group_membership,
    get_group_membership_by_id,
    group_info,
    modify_group,
    remove_user_group,
)
from krs.institutions import Region, create_inst
from krs.users import create_user

# noinspection PyUnresolvedReferences
from ..util import keycloak_bootstrap  # type: ignore


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
    await add_user_group('/institutions/Experiment1/Good/authorlist-special', u_add_to_authors, rest_client=keycloak_bootstrap)

    u_remain_in_authors = 'remain-in-authors'
    await create_user(u_remain_in_authors, **user_kwargs.pop())
    await add_user_group('/institutions/Experiment1/Good', u_remain_in_authors, rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Good/authorlist', u_remain_in_authors, rest_client=keycloak_bootstrap)
    for group in all_synchronized_groups:
        await add_user_group(group, u_remain_in_authors, rest_client=keycloak_bootstrap)

    u_remove_bc_in_disabled = 'remove-in-disabled-authorlist'
    await create_user(u_remove_bc_in_disabled, **user_kwargs.pop())
    await add_user_group('/institutions/Experiment1/Authorlist_false', u_remove_bc_in_disabled, rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/Experiment1/Authorlist_false/authorlist', u_remove_bc_in_disabled, rest_client=keycloak_bootstrap)
    for group in all_synchronized_groups:
        await add_user_group(group, u_remove_bc_in_disabled, rest_client=keycloak_bootstrap)

    u_dont_add_bc_wrong_expt = 'dont-add-wrong-experiment'
    await create_user(u_dont_add_bc_wrong_expt, **user_kwargs.pop())
    await add_user_group('/institutions/ExperimentXXX/Irrelevant', u_dont_add_bc_wrong_expt, rest_client=keycloak_bootstrap)
    await add_user_group('/institutions/ExperimentXXX/Irrelevant/authorlist', u_dont_add_bc_wrong_expt, rest_client=keycloak_bootstrap)

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
async def test_group_id_by_path(keycloak_bootstrap):
    await create_group('/g1', rest_client=keycloak_bootstrap)
    await create_group('/g1/g2', rest_client=keycloak_bootstrap)

    expected_id = (await group_info('/g1/g2', rest_client=keycloak_bootstrap))['id']
    assert await group_id_by_path('/g1/g2', keycloak_bootstrap) == expected_id

    with pytest.raises(GroupDoesNotExist):
        await group_id_by_path('/nonexistent', keycloak_bootstrap)


@pytest.mark.asyncio
async def test_get_group_membership_cached(keycloak_bootstrap):
    await create_group('/g1', rest_client=keycloak_bootstrap)
    await create_user('testuser1', first_name='F', last_name='L', email='u1@test', rest_client=keycloak_bootstrap)
    await add_user_group('/g1', 'testuser1', rest_client=keycloak_bootstrap)

    assert await get_group_membership_cached('/g1', keycloak_bootstrap) == ['testuser1']

    with pytest.raises(GroupDoesNotExist):
        await get_group_membership_cached('/nonexistent', keycloak_bootstrap)


@pytest.mark.asyncio
async def test_target_group_own_membership_read_bypasses_shared_cache(keycloak_bootstrap):
    # sync_synchronized_group() must read a target group's OWN current membership
    # fresh, not via get_group_membership_cached() -- that cache is shared with
    # source-group lookups done for OTHER synchronized groups in the same run, so
    # caching a target's pre-sync snapshot there would leak stale membership to
    # any group that later uses this same group as a source group.
    await create_group('/chain', rest_client=keycloak_bootstrap)
    await create_user('extraneous1', first_name='F', last_name='L', email='ext1@test', rest_client=keycloak_bootstrap)
    await add_user_group('/chain', 'extraneous1', rest_client=keycloak_bootstrap)

    # Populate the shared cache, as a sibling group's source-group lookup would.
    assert await get_group_membership_cached('/chain', keycloak_bootstrap) == ['extraneous1']

    # Mutate /chain's membership directly, as sync_synchronized_group() would
    # while processing /chain as a target -- the cache above is now stale.
    await remove_user_group('/chain', 'extraneous1', rest_client=keycloak_bootstrap)

    # The read sync_synchronized_group() uses for a target's own current_members
    # must see the fresh state, not the stale cache entry populated above.
    fresh_members = await get_group_membership_by_id(
        await group_id_by_path('/chain', keycloak_bootstrap), rest_client=keycloak_bootstrap)
    assert fresh_members == []


@pytest.mark.asyncio
async def test_dependent_sync_sees_fresh_membership_of_prior_target(keycloak_bootstrap):
    # End-to-end version of the above: a group that is itself synced as a target
    # and is also the SOURCE group of another synchronized group must have its
    # post-sync (not pre-sync) membership visible when that other group is synced
    # afterward in the same process/caches.
    auto_sync_attr = fields(SyncGroupConfig).auto_sync.metadata['attr']
    policy_attr = fields(SyncGroupConfig).policy.metadata['attr']
    attrs = {auto_sync_attr: 'false', policy_attr: MembershipSyncPolicy.match.value}

    await create_group('/root', rest_client=keycloak_bootstrap)
    await create_group('/root/base', rest_client=keycloak_bootstrap)
    await create_group('/root/chain', rest_client=keycloak_bootstrap, attrs=attrs)
    await create_group('/root/dst', rest_client=keycloak_bootstrap, attrs=attrs)

    await create_user('extraneous1', first_name='F', last_name='L', email='ext1@test', rest_client=keycloak_bootstrap)
    # extraneous1 is in /root/chain but not in /root/base, so syncing /root/chain
    # against /root/base (its source) must prune them.
    await add_user_group('/root/chain', 'extraneous1', rest_client=keycloak_bootstrap)

    await manual_group_sync('/root/chain', "$..subGroups[?path == '/root/base'].path",
                            keycloak_client=keycloak_bootstrap, allow_notifications=False, dryrun=False)

    # /root/dst sources from /root/chain, synced immediately above in this same run.
    # With policy=match, if /root/dst's source-group lookup of /root/chain sees a
    # stale (pre-prune) membership, it would wrongly add extraneous1 to /root/dst.
    await manual_group_sync('/root/dst', "$..subGroups[?path == '/root/chain'].path",
                            keycloak_client=keycloak_bootstrap, allow_notifications=False, dryrun=False)

    assert await get_group_membership('/root/dst', rest_client=keycloak_bootstrap) == []


@pytest.mark.asyncio
async def test_auto_sync_does_not_refetch_group_info_per_group(keycloak_bootstrap, monkeypatch):
    # auto_sync_enabled_groups() already has every group's attributes from its
    # initial list_groups() call and must not re-fetch them via group_info() per
    # enabled group (which would also uselessly populate that group's subgroups).
    auto_sync_attr = fields(SyncGroupConfig).auto_sync.metadata['attr']
    policy_attr = fields(SyncGroupConfig).policy.metadata['attr']
    sources_expr_attr = fields(SyncGroupConfig).sources_expr.metadata['attr']
    # No matching source groups and policy=prune, so processing each group is a
    # true no-op: no member ever needs a deferred-removal check, so nothing else
    # in sync_synchronized_group() calls group_info() either -- any call seen
    # here can only come from the group-discovery loop under test.
    attrs = {auto_sync_attr: 'true', policy_attr: MembershipSyncPolicy.prune.value,
             sources_expr_attr: "$..subGroups[?path == '/nonexistent-source'].path"}

    await create_group('/g1', rest_client=keycloak_bootstrap, attrs=attrs)
    await create_group('/g2', rest_client=keycloak_bootstrap, attrs=attrs)

    calls = []
    real_group_info = sync_synchronized_groups_module.group_info

    async def spying_group_info(*args, **kwargs):
        calls.append(args)
        return await real_group_info(*args, **kwargs)

    monkeypatch.setattr(sync_synchronized_groups_module, 'group_info', spying_group_info)

    await auto_sync_enabled_groups(keycloak_bootstrap, allow_notifications=False, dryrun=False)

    assert calls == []


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
    monkeypatch.setattr(sync_synchronized_groups_module, 'get_rest_client', MagicMock)

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
