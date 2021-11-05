import pytest

import actions.util

class TestException(Exception):
    __test__ = False

@pytest.fixture
def patch_ssh(mocker):
    return mocker.patch('actions.util.scp_and_run')