"""
Institution actions against Keycloak.
"""
import asyncio
from enum import Enum
import json
import logging

from .users import _fix_attributes
from . import groups
from .token import get_rest_client

logger = logging.getLogger('krs.institutions')


class Region(Enum):
    """Institution region"""
    NORTH_AMERICA = "North America"
    EUROPE = "Europe"
    ASIA_PAC = "Asia Pacific"


async def list_insts(experiment=None, filter_func=None, rest_client=None):
    """
    List institution group_paths in Keycloak.

    Args:
        experiment (str): experiment name (default: list all experiments)
        filter_func (callable): given a group path and set of attrs, a callable to return true/false

    Returns:
        dict: group_path: attrs
    """
    url = '/groups?briefRepresentation=false&max=10000'
    group_hierarchy = await rest_client.request('GET', url)
    logger.debug('raw list_insts: %r', group_hierarchy)
    ret = {}

    def add_groups(groups):
        for g in groups:
            if g['subGroups']:
                add_groups(g['subGroups'])
            parts = g['path'].split('/')
            if len(parts) == 4 and parts[1] == 'institutions':
                # this is an institution group
                if experiment and parts[2] != experiment:
                    continue
                _fix_attributes(g)
                authorlists = {}
                for subg in g['subGroups']:
                    if subg['name'].startswith('authorlist-'):
                        _fix_attributes(subg)
                        authorlists[subg['name'].replace('authorlist-', '')] = subg['attributes'].get('cite', '')
                if authorlists:
                    g['attributes']['authorlists'] = authorlists
                if callable(filter_func) and not filter_func(g['path'], g['attributes']):
                    continue
                ret[g['path']] = g['attributes']
    add_groups(group_hierarchy)

    return {k: ret[k] for k in sorted(ret)}


class InstitutionAttrsMismatchError(RuntimeError):
    pass


async def list_insts_flat(experiment=None, filter_func=None, remove_empty=True, attr_whitelist=None, rest_client=None):
    """
    List institution names in Keycloak, removing overlaps from multiple experiments.

    Args:
        experiment (str): experiment name (default: list all experiments)
        filter_func (callable): given a group path and set of attrs, a callable to return true/false
        remove_empty (bool): remove institutions with no attributes
        attr_whitelist (iterable): whitelist of attributes (default: all)

    Returns:
        dict: name: attrs
    """
    raw = await list_insts(experiment, filter_func=filter_func, rest_client=rest_client)
    ret = {}
    for path in sorted(raw):
        inst_key = path.split('/')[-1]
        attrs = raw[path]
        if remove_empty and not attrs:
            logger.info(f'ignoring inst {path} with no attrs')
            continue
        if attr_whitelist:
            attrs = {k: attrs[k] for k in attrs if k in attr_whitelist}
        if inst_key in ret and ret[inst_key] != attrs:
            logger.warning(f'inst attr mismatch - {inst_key}')
            for path in raw:
                if path.split('/')[-1] == inst_key:
                    logger.info(f'{path} {raw[path]}')
            raise InstitutionAttrsMismatchError(inst_key)
        ret[inst_key] = attrs
    return ret


async def inst_info(experiment, institution, rest_client=None):
    """
    Get institution information.

    Args:
        experiment (str): experiment name
        institution (str): institution name

    Returns:
        dict: attribute info
    """
    group_path = f'/institutions/{experiment}/{institution}'
    ret = await list_insts(experiment, rest_client=rest_client)
    if group_path not in ret:
        raise KeyError(f'inst "{group_path}" does not exist')
    return ret[group_path]


def validate_attrs(attrs):
    if not attrs:
        raise ValueError('attrs is required')
    for n in ('name', 'cite', 'abbreviation', 'is_US', 'region'):
        if n not in attrs:
            raise KeyError(f'{n} is required in attrs')
    if isinstance(attrs['region'], Region):
        attrs['region'] = attrs['region'].value
    else:
        Region(attrs['region'])  # this will raise a ValueError if not a Region
    if 'authorlist' not in attrs:
        attrs['authorlist'] = False
    if 'has_mou' not in attrs:
        attrs['has_mou'] = False
    return attrs


async def create_inst(experiment, institution, attrs=None, rest_client=None):
    """
    Create an institution in Keycloak.

    Requred attributes:
        name (str): name of institution
        cite (str): citation string
        abbreviation (str): abbreviation
        is_US (bool): if institution is on US NSF funding
        region (Region): a value from the Region enum

    Optional attributes:
        authorlist (bool): is this an active authorlist inst?
        authorlists (dict): multiple authorlists with different citations
        has_mou (bool): is this an active MOU inst?

    Args:
        experiment (str): experiment name
        institution (str): institution name
        attrs (dict): attributes
    """
    attrs = validate_attrs(attrs)
    authorlists = attrs.pop('authorlists', None)

    group_path = f'/institutions/{experiment}/{institution}'
    await groups.create_group(group_path, attrs=attrs, rest_client=rest_client)
    await groups.create_group(f'{group_path}/_admin', attrs=attrs, rest_client=rest_client)

    if authorlists:
        for name in authorlists:
            attrs = {'cite': authorlists[name]}
            await groups.create_group(f'{group_path}/authorlist-{name}',
                                      attrs=attrs, rest_client=rest_client)
    elif attrs['authorlist']:
        await groups.create_group(f'{group_path}/authorlist', rest_client=rest_client)


async def modify_inst(experiment, institution, attrs, rest_client=None):
    """
    Modify attributes for an institution.

    Patches attributes with existing ones.  Use `None` to remove attr.

    Does not handle authorlist subgroups.

    Args:
        experiment (str): experiment name
        institution (str): institution name
        attrs (dict): attributes to modify
    """
    attrs.pop('authorlists', None)

    existing_attrs = await inst_info(experiment, institution, rest_client=rest_client)
    existing_attrs.pop('authorlsits', None)

    new_attrs = existing_attrs.copy()
    new_attrs.update(attrs)

    new_attrs = validate_attrs(new_attrs)

    group_path = f'/institutions/{experiment}/{institution}'
    await groups.modify_group(group_path, attrs=new_attrs, rest_client=rest_client)


def main():
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='Keycloak institution management')
    subparsers = parser.add_subparsers()
    parser_list = subparsers.add_parser('list', help='list institutions by group path')
    parser_list.add_argument('--experiment', help='experiment name')
    parser_list.set_defaults(func=list_insts)
    parser_list_flat = subparsers.add_parser('list-name', help='list institutions by name only')
    parser_list_flat.add_argument('--experiment', help='experiment name')
    parser_list_flat.add_argument('--attr', dest='attr_whitelist', action='append', help='attribute names to compare (one per arg)')
    parser_list_flat.set_defaults(func=list_insts_flat)
    parser_info = subparsers.add_parser('info', help='institution info')
    parser_info.add_argument('experiment', help='experiment name')
    parser_info.add_argument('institution', help='institution name')
    parser_info.set_defaults(func=inst_info)
    parser_create = subparsers.add_parser('create', help='create a new institution')
    parser_create.add_argument('experiment', help='experiment name')
    parser_create.add_argument('institution', help='institution name')
    parser_create.add_argument('attrs', type=json.loads, help='attributes')
    parser_create.set_defaults(func=create_inst)
    parser_modify = subparsers.add_parser('modify', help='modify an institution\'s attributes')
    parser_modify.add_argument('experiment', help='experiment name')
    parser_modify.add_argument('institution', help='institution name')
    parser_modify.add_argument('attrs', type=json.loads, help='attributes')
    parser_modify.set_defaults(func=modify_inst)
    args = vars(parser.parse_args())

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    rest_client = get_rest_client()
    func = args.pop('func')
    ret = asyncio.run(func(rest_client=rest_client, **args))
    if ret is not None:
        pprint(ret)


if __name__ == '__main__':
    main()
