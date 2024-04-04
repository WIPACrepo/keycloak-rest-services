import pytest

from packaging import version

from krs import util

from ..util import keycloak_bootstrap  # type: ignore


@pytest.mark.asyncio
async def test_keycloak_version(keycloak_bootstrap):
    ver = await util.keycloak_version(rest_client=keycloak_bootstrap)
    version.parse(ver)
    # Check that our rest client is still functional
    ret = await keycloak_bootstrap.request('GET', '/')
    assert 'realm' in ret
