import os

import pytest

from packaging import version
from rest_tools.client import RestClient

from krs import bootstrap, util

from ..util import keycloak_bootstrap  # type: ignore


@pytest.mark.asyncio
async def test_keycloak_version(keycloak_bootstrap):
    # As of Keycloak 26.7, /serverinfo only includes systemInfo (which carries
    # the version) for accounts holding manage-realm in the master realm, so
    # a realm-scoped service account like keycloak_bootstrap's can't see it.
    master_admin = RestClient(
        f'{os.environ["KEYCLOAK_URL"]}/auth/admin/realms/master',
        token=bootstrap.get_token(),
        retries=0,
    )
    ver = await util.keycloak_version(rest_client=master_admin)
    version.parse(ver)
    # Check that our rest client is still functional
    ret = await master_admin.request('GET', '/')
    assert 'realm' in ret
