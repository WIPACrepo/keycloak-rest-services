import argparse
import asyncio
from collections import defaultdict
from xml.etree import ElementTree
from html import unescape
import logging

import requests

from krs.users import list_users, modify_user
from krs.groups import add_user_group
from krs.token import get_rest_client

from .institution_list import ICECUBE_INSTS, GEN2_INSTS

logger = logging.getLogger('import_authorlist')


IGNORE_LIST = set(['IceCube', 'wipac'])


def get_attr_as_list(group, name, default=None):
    if name not in group:
        return default
    val = group[name]
    if isinstance(val, list):
        return val
    return [val]


async def import_authorlist_insts(keycloak_conn, base_group='/institutions/IceCube', INSTS=ICECUBE_INSTS, dryrun=False):
    # get authorlist data
    url = f'https://authorlist.icecube.wisc.edu/api/authors?formatting=inspire&collab={base_group.split("/")[-1]}'
    r = requests.get(url)
    inspire_xml = unescape(r.json()['inspire']['format_text'])
    author_data = ElementTree.fromstring(inspire_xml)
    author_insts = {}
    author_users = []
    for el in author_data.iter():
        if el.tag == '{http://xmlns.com/foaf/0.1/}Organization':
            author_insts[el.attrib['id']] = el.find('{http://xmlns.com/foaf/0.1/}name').text
        elif el.tag == '{http://xmlns.com/foaf/0.1/}Person':
            aff = el.find('{http://inspirehep.net/info/HepNames/tools/authors_xml/}authorAffiliations')
            ids = el.find('{http://inspirehep.net/info/HepNames/tools/authors_xml/}authorids')
            author_users.append({
                'first': el.find('{http://xmlns.com/foaf/0.1/}givenName').text,
                'last': el.find('{http://xmlns.com/foaf/0.1/}familyName').text,
                'author': el.find('{http://inspirehep.net/info/HepNames/tools/authors_xml/}authorNamePaper').text,
                'insts': [e.attrib['organizationid'] for e in aff if 'connection' not in e.attrib],
                'thanks': [e.attrib['organizationid'] for e in aff if 'connection' in e.attrib],
                'email': [e.text for e in ids if e.attrib['source'] == 'INTERNAL'],
            })

    authors_by_inst = defaultdict(list)
    for user in author_users:
        for inst in user['insts']:
            authors_by_inst[author_insts[inst]].append(user)

    keycloak_users = await list_users(rest_client=keycloak_conn)
    keycloak_by_last = defaultdict(list)
    for ku in keycloak_users.values():
        keycloak_by_last[ku['lastName']].append(ku)

    for inst in INSTS:
        group_name = f'{base_group}/{inst}/authorlist'
        cite = INSTS[inst]['cite']

        if cite not in authors_by_inst:
            logger.warning(f'skipping inst {inst}, not in author list')
            continue
        if not authors_by_inst[cite]:
            logger.warning(f'inst {inst} has no authors')
            continue

        for user in authors_by_inst[cite]:
            # figure out who this is
            if user['last'] in keycloak_by_last:
                ku = keycloak_by_last[user['last']]
                if len(ku) == 1:
                    keycloak_user = ku[0]
                else:
                    for u in ku:
                        if u['firstName'] == user['first']:
                            keycloak_user = u
                            break
                        parts = user['email'].split('@')
                        if len(parts) == 2 and parts[1] == 'icecube.wisc.edu' and parts[0] == u['username']:
                            keycloak_user = u
                            break
                    else:
                        logger.warning(f'unknown user {user["first"]} {user["last"]} in {inst}')
                        continue
            else:
                logger.warning(f'unknown user {user["first"]} {user["last"]} in {inst}')
                continue

            logger.info(f'adding {user["first"]} {user["last"]}: {keycloak_user["username"]} to {inst}')  # lgtm [py/clear-text-logging-sensitive-data]
            if not dryrun:
                await add_user_group(group_name, keycloak_user['username'], rest_client=keycloak_conn)
                attrs = {'author_name': user['author']}
                await modify_user(keycloak_user['username'], attrs, rest_client=keycloak_conn)


def main():
    parser = argparse.ArgumentParser(description='IceCube Keycloak setup')
    parser.add_argument('--dryrun', action='store_true', help='dry run')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    rest_client = get_rest_client()
    asyncio.run(import_authorlist_insts(rest_client, dryrun=args.dryrun))
    asyncio.run(import_authorlist_insts(rest_client, base_group='/institutions/IceCube-Gen2', INSTS=ICECUBE_INSTS, dryrun=args.dryrun))
    asyncio.run(import_authorlist_insts(rest_client, base_group='/institutions/IceCube-Gen2', INSTS=GEN2_INSTS, dryrun=args.dryrun))


if __name__ == '__main__':
    main()
