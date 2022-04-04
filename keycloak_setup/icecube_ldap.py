import argparse
import asyncio
import logging

from krs.ldap import LDAP, get_ldap_members
from krs.users import UserDoesNotExist
from krs.groups import list_groups, create_group, modify_group, add_user_group, remove_user_group
from krs.bootstrap import get_token
from krs.token import get_rest_client

from .institution_list import ICECUBE_INSTS, GEN2_INSTS

logger = logging.getLogger('import_ldap')


IGNORE_LIST = set(['IceCube', 'wipac'])


def get_attr_as_list(group, name, default=None):
    if name not in group:
        return default
    val = group[name]
    if isinstance(val, list):
        return val
    return [val]


async def import_ldap_groups(keycloak_conn, ldap_setup=True, dryrun=False):
    ldap_conn = LDAP()

    if ldap_setup:
        # start with LDAP setup
        await ldap_conn.keycloak_ldap_link(get_token())
        await ldap_conn.force_keycloak_sync(keycloak_client=keycloak_conn)

    ldap_users = ldap_conn.list_users()
    ldap_groups = ldap_conn.list_groups()

    keycloak_groups = await list_groups(rest_client=keycloak_conn)

    # handle /posix group
    if '/posix' not in keycloak_groups:
        logger.info('creating /posix group')
        if not dryrun:
            await create_group('/posix', rest_client=keycloak_conn)
    if not dryrun:
        for member in ldap_users:
            try:
                if 'loginShell' in ldap_users[member] and ldap_users[member]['loginShell'] != '/sbin/nologin':
                    logger.info(f'add {member} to /posix')
                    await add_user_group('/posix', member, rest_client=keycloak_conn)
                else:
                    logger.info(f'remove {member} from /posix')
                    await remove_user_group('/posix', member, rest_client=keycloak_conn)
            except UserDoesNotExist:
                logger.info(f'skipping user {member} for group /posix - user does not exist')

    for group_name in sorted(ldap_groups):
        members = get_ldap_members(ldap_groups[group_name])
        gidNumber = ldap_groups[group_name]['gidNumber']

        if group_name in IGNORE_LIST:
            logger.info(f'skipping ignored group {group_name}')
        elif not members:
            logger.info(f'skipping empty group {group_name}')
        elif f'/posix/{group_name}' in keycloak_groups:
            logger.info(f'skipping existing group {group_name}')
        elif group_name in ldap_users:
            # this is a user group
            if members == [group_name]:
                logger.info(f'skipping 1:1 user group {group_name}')
            else:
                logger.info(f'creating user group /posix/{group_name} with members {members}')
                if not dryrun:
                    await create_group(f'/posix/{group_name}', {'gidNumber': gidNumber}, rest_client=keycloak_conn)
                    for member in members:
                        try:
                            await add_user_group(f'/posix/{group_name}', member, rest_client=keycloak_conn)
                        except UserDoesNotExist:
                            logger.info(f'skipping user {member} for group /posix/{group_name} - user does not exist')
        else:
            logger.info(f'creating non-user group /posix/{group_name} with members {members}')
            if not dryrun:
                await create_group(f'/posix/{group_name}', {'gidNumber': gidNumber}, rest_client=keycloak_conn)
                for member in members:
                    try:
                        await add_user_group(f'/posix/{group_name}', member, rest_client=keycloak_conn)
                    except UserDoesNotExist:
                        logger.info(f'skipping user {member} for group /posix/{group_name} - user does not exist')


async def import_ldap_insts(keycloak_conn, base_group='/institutions/IceCube', INSTS=ICECUBE_INSTS, dryrun=False):
    ldap_conn = LDAP()
    ldap_users = ldap_conn.list_users()

    # now handle institutions
    keycloak_insts_by_o = {}
    for name in INSTS:
        if '_ldap_o' in INSTS[name]:
            inst = INSTS[name].copy()
            inst['name'] = name
            keycloak_insts_by_o[inst['_ldap_o']] = inst
        else:
            logger.info(f'skipping Keycloak inst {name}')

    inst_groups = ldap_conn.list_groups('ou=Institutions,dc=icecube,dc=wisc,dc=edu')
    for inst_cn in sorted(inst_groups, key=lambda x: inst_groups[x]['o']):
        inst = inst_groups[inst_cn]
        inst_o = inst['o']

        if inst_o in keycloak_insts_by_o:
            keycloak_inst = keycloak_insts_by_o[inst_o]
            logger.info(f'syncing inst {keycloak_inst["name"]}')
            keycloak_group = f'{base_group}/{keycloak_inst["name"]}'

            inst_security_contact = get_attr_as_list(inst, 'collaboratorSecurityContact', default=[])
            inst_admin = get_attr_as_list(inst, 'institutionLeadUid', default=[])

            attrs = {
                'collaboratorSecurityContact': inst_security_contact,
                'institutionLeadUid': inst_admin,
            }
            if not dryrun:
                logger.info(f'modify inst with attrs {attrs}')
                await modify_group(keycloak_group, attrs, rest_client=keycloak_conn)
            for user in inst_admin:
                logger.debug(f'adding admin user {user} to {keycloak_group}/_admin')
                if not dryrun:
                    await add_user_group(keycloak_group+'/_admin', user, rest_client=keycloak_conn)
            inst_full_o = f'o={inst_o},ou=Institutions,dc=icecube,dc=wisc,dc=edu'
            for user in ldap_users:
                if ldap_users[user].get('o', None) == inst_full_o:
                    logger.debug(f'adding user {user} to {keycloak_group}')
                    if not dryrun:
                        await add_user_group(keycloak_group, user, rest_client=keycloak_conn)
        else:
            logger.info(f'skipping LDAP inst {inst["o"]}')


def main():
    parser = argparse.ArgumentParser(description='IceCube Keycloak setup')
    parser.add_argument('--dryrun', action='store_true', help='dry run')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    rest_client = get_rest_client()
    asyncio.run(import_ldap_groups(rest_client, ldap_setup=False, dryrun=args.dryrun))
    asyncio.run(import_ldap_insts(rest_client, dryrun=args.dryrun))
    asyncio.run(import_ldap_insts(rest_client, base_group='/institutions/IceCube-Gen2', INSTS=ICECUBE_INSTS, dryrun=args.dryrun))
    asyncio.run(import_ldap_insts(rest_client, base_group='/institutions/IceCube-Gen2', INSTS=GEN2_INSTS, dryrun=args.dryrun))


if __name__ == '__main__':
    main()
