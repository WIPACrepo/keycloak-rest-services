import smtplib
from contextlib import AbstractContextManager
from unittest.mock import MagicMock

import pytest

import krs.email


class MockResponse(AbstractContextManager, MagicMock):
    def __exit__(self, *args):
        pass
    send_message = MagicMock()


@pytest.fixture
def patch_smtp(mocker):
    return mocker.patch('smtplib.SMTP', new=MockResponse())


def test_send_email(patch_smtp):
    krs.email.send_email('foo@bar', 'test', 'test message')

    patch_smtp.assert_called()
    patch_smtp.return_value.send_message.assert_called()
    a = patch_smtp.return_value.send_message.call_args[0][0]
    assert 'To: foo@bar' in str(a)
    assert 'Subject: test' in str(a)
    assert 'test message' in str(a)


def test_send_email_no_domain(patch_smtp):
    krs.email.send_email('foo', 'test', 'test message')

    patch_smtp.assert_called()
    patch_smtp.return_value.send_message.assert_called()
    a = patch_smtp.return_value.send_message.call_args[0][0]
    assert 'To: foo' in str(a)
    assert 'Subject: test' in str(a)
    assert 'test message' in str(a)
