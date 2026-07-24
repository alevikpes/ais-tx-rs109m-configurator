import pytest

from src.configurator import Configurator


class TestConfigurator:

    # Test SerialProtocol by Mocking it.
    #@staticmethod
    #def test_command_retry(mocker):
    #    fake = mocker.Mock()
    #    fake.read.side_effect = [b'bad', b'\x95\x20']
    #    protocol = object.__new__(SerialProtocol)
    #    protocol.serial = fake

    #    response = protocol._command(b'test', b'\x95\x20')
    #    assert response == b'\x95\x20'

    @pytest.mark.parametrize(
        'field,max_value',
        [
            ('ais2bow', 511),
            ('ais2stern', 511),
            ('ais2port', 63),
            ('ais2star', 63),
        ],
    )
    @staticmethod
    def test_ais_positions_roundtrip(field, max_value):
        c = Configurator()
        for value in (0, 1, max_value // 2, max_value):
            setattr(c, field, value)
            assert getattr(c, field) == value

    @pytest.mark.parametrize(
        'field,max_value',
        [
            ('ais2bow', 511),
            ('ais2stern', 511),
            ('ais2port', 63),
            ('ais2star', 63),
        ],
    )
    @staticmethod
    def test_ais_positions_invalid(field, max_value):
        c = Configurator()
        for value in (-1, max_value + 1):
            with pytest.raises(ValueError):
                setattr(c, field, value)

    @staticmethod
    @pytest.mark.parametrize(
        'field,config,expected',
        [
            ('ais2bow', {38: 0x3f, 39: 0xe0}, 511),
            ('ais2stern', {39: 0x1f, 40: 0xf0}, 511),
            ('ais2port', {40: 0x0f, 41: 0xc0}, 63),
            ('ais2star', {41: 0x3f}, 63),
        ],
    )
    def test_decode(field, config, expected):
        c = Configurator()
        for index, value in config.items():
            c._config[index] = value

        assert getattr(c, field) == expected
