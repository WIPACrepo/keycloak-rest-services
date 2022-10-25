import pytest

from krs.token import get_token
from krs import groups, institutions, users

from ..util import keycloak_bootstrap

@pytest.mark.asyncio
async def test_list_insts(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)

    # first test with no insts
    ret = await institutions.list_insts(rest_client=keycloak_bootstrap)
    assert ret == {}

    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test', rest_client=keycloak_bootstrap)

    ret = await groups.list_groups(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['/institutions', '/institutions/IceCube', '/institutions/IceCube/Test']

    ret = await institutions.list_insts(rest_client=keycloak_bootstrap)
    assert ret == {'/institutions/IceCube/Test': {}}

    ret = await institutions.list_insts('IceCube', rest_client=keycloak_bootstrap)
    assert ret == {'/institutions/IceCube/Test': {}}

    ret = await institutions.list_insts('Other', rest_client=keycloak_bootstrap)
    assert ret == {}

@pytest.mark.asyncio
async def test_list_insts_flat(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)

    # first test with no insts
    ret = await institutions.list_insts_flat(rest_client=keycloak_bootstrap)
    assert ret == {}

    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube2', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube2/Test', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube2/Test2', rest_client=keycloak_bootstrap)
    ret = await institutions.list_insts_flat(remove_empty=False, rest_client=keycloak_bootstrap)
    assert ret == {'Test': {}, 'Test2': {}}

    ret = await institutions.list_insts_flat('IceCube', remove_empty=False, rest_client=keycloak_bootstrap)
    assert ret == {'Test': {}}

    ret = await institutions.list_insts_flat('Other', remove_empty=False, rest_client=keycloak_bootstrap)
    assert ret == {}

    await groups.create_group('/institutions/IceCube/Test2', {'foo': 'bar'}, rest_client=keycloak_bootstrap)
    with pytest.raises(institutions.InstitutionAttrsMismatchError):
        await institutions.list_insts_flat(remove_empty=False, rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_list_insts_flat_whitelist(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)

    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test', {'foo': 'bar'}, rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube2', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube2/Test', {'foo': 'bar'}, rest_client=keycloak_bootstrap)
    ret = await institutions.list_insts_flat(rest_client=keycloak_bootstrap)
    assert ret == {'Test': {'foo': 'bar'}}

    await groups.create_group('/institutions/IceCube/Test2', {'bar': 'baz'}, rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube2/Test2', {'bar': 'foo'}, rest_client=keycloak_bootstrap)
    with pytest.raises(institutions.InstitutionAttrsMismatchError):
        await institutions.list_insts_flat(rest_client=keycloak_bootstrap)
    ret = await institutions.list_insts_flat(attr_whitelist=['foo'], rest_client=keycloak_bootstrap)
    assert ret == {'Test': {'foo': 'bar'}, 'Test2': {}}

@pytest.mark.asyncio
async def test_list_insts_filter(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test', {'foo': '1'}, rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test2', {'foo': '2'}, rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test3', {'bar': '2'}, rest_client=keycloak_bootstrap)
    ret = await institutions.list_insts_flat(filter_func=lambda n,a: a.get('foo') == '1', rest_client=keycloak_bootstrap)
    assert ret == {'Test': {'foo': '1'}}

@pytest.mark.asyncio
async def test_inst_info(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube/Test', {'foo': '1'}, rest_client=keycloak_bootstrap)
    ret = await institutions.inst_info('IceCube', 'Test', rest_client=keycloak_bootstrap)
    assert ret == {'foo': '1'}

    await groups.create_group('/institutions/IceCube/Test/authorlist-foo', {'cite': 'abc'}, rest_client=keycloak_bootstrap)
    ret = await institutions.inst_info('IceCube', 'Test', rest_client=keycloak_bootstrap)
    assert ret == {'foo': '1', 'authorlists': {'foo': 'abc'}}

@pytest.mark.asyncio
async def test_create_inst(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)

    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'T', 'is_US': False, 'region': institutions.Region.NORTH_AMERICA}
    await institutions.create_inst('IceCube', 'Test', attrs, rest_client=keycloak_bootstrap)
    ret = await institutions.list_insts_flat(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['Test']

    attrs = {'name': 'Test2', 'cite': 'Test2', 'abbreviation': 'TT', 'is_US': False, 'region': 'Asia Pacific'}
    await institutions.create_inst('IceCube', 'Test2', attrs, rest_client=keycloak_bootstrap)
    ret = await institutions.list_insts_flat(rest_client=keycloak_bootstrap)
    assert list(ret.keys()) == ['Test', 'Test2']

    with pytest.raises(ValueError):
        await institutions.create_inst('IceCube', 'Test3', {}, rest_client=keycloak_bootstrap)

    with pytest.raises(KeyError):
        await institutions.create_inst('IceCube', 'Test3', {'name':'Test3'}, rest_client=keycloak_bootstrap)

    attrs = {'name': 'Test2', 'cite': 'Test2', 'abbreviation': 'TT', 'is_US': False, 'region': 'Bad'}
    with pytest.raises(ValueError):
        await institutions.create_inst('IceCube', 'Test3', attrs, rest_client=keycloak_bootstrap)

@pytest.mark.asyncio
async def test_modify_inst(keycloak_bootstrap):
    await groups.create_group('/institutions', rest_client=keycloak_bootstrap)
    await groups.create_group('/institutions/IceCube', rest_client=keycloak_bootstrap)

    attrs = {'name': 'Test', 'cite': 'Test', 'abbreviation': 'T', 'is_US': False, 'region': institutions.Region.NORTH_AMERICA}
    await institutions.create_inst('IceCube', 'Test', attrs, rest_client=keycloak_bootstrap)

    attrs = {'has_mou': 'true'}
    await institutions.modify_inst('IceCube', 'Test', attrs, rest_client=keycloak_bootstrap)

    ret = await institutions.inst_info('IceCube', 'Test', rest_client=keycloak_bootstrap)
    assert 'has_mou' in ret
    assert ret['has_mou'] == 'true'
