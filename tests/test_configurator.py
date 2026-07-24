import pytest

from main import Configurator


# Test SerialProtocol by Mocking it.
def test_command_retry(mocker):
    fake = mocker.Mock()
    fake.read.side_effect = [b'bad', b'\x95\x20']
    protocol = object.__new__(SerialProtocol)
    protocol.serial = fake

    response = protocol._command(b'test', b'\x95\x20')
    assert response == b'\x95\x20'
