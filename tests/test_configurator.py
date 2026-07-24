import pytest

from src.configurator import Configurator


class TestConfigurator:

    # Test SerialProtocol by Mocking it.
    @staticmethod
    def test_command_retry(mocker):
        fake = mocker.Mock()
        fake.read.side_effect = [b'bad', b'\x95\x20']
        protocol = object.__new__(SerialProtocol)
        protocol.serial = fake

        response = protocol._command(b'test', b'\x95\x20')
        assert response == b'\x95\x20'

    @pytest.mark.parametrize('x', [1, 2, 3, 4, 5, 6, 7])
    @staticmethod
    def test_roundtrip_bit_values(x):
        c = Configurator()
        values = bytearray(
            value & ((1 << x) - 1)
            for value in range(1, 20)
        )

        encoded = c._toxbit(values, x=x, digitalphaencoding=False)
        decoded = c._fromxbit(encoded, x=x, digitalphaencoding=False)

        assert decoded[:len(values)] == values

    @staticmethod
    def test_roundtrip_digitalpha():
        c = Configurator()
        s = bytearray(b'ABC123')

        encoded = c._toxbit(s)
        decoded = c._fromxbit(encoded)

        assert decoded.decode('ascii') == s

    @staticmethod
    def test_digitalpha_converts_lowercase():
        c = Configurator()
        encoded = c._toxbit('abc123')
        decoded = c._fromxbit(encoded)

        assert decoded.decode('ascii') == 'ABC123'

    @staticmethod
    def test_empty_input_toxbit():
        c = Configurator()
        assert c._toxbit('') == [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]

    @staticmethod
    def test_empty_input_fromxbit():
        c = Configurator()
        with pytest.raises(ValueError, match='Must supply non-empty array'):
            c._fromxbit(bytearray())

    @pytest.mark.parametrize('x', [0, 8])
    @staticmethod
    def test_invalid_bit_length_fromxbit(x):
        c = Configurator()
        with pytest.raises(ValueError, match='BitLen must between 1 and 7'):
            c._fromxbit(bytearray([0]), x=x)

    @pytest.mark.parametrize('x', [0, 8])
    @staticmethod
    def test_invalid_bit_length_toxbit(x):
        c = Configurator()
        with pytest.raises(ValueError, match='BitLen must between 1 and 7'):
            c._toxbit('ABC', x=x)

    @staticmethod
    def test_known_6bit_encoding():
        c = Configurator()
        encoded = c._toxbit('ABC')
        decoded = c._fromxbit(encoded)

        assert decoded.decode('ascii') == 'ABC'

    @staticmethod
    def test_known_single_character():
        c = Configurator()
        encoded = c._toxbit('A')
        decoded = c._fromxbit(encoded)

        assert decoded.decode('ascii') == 'A'

    @staticmethod
    def test_fromxbit_without_digitalpha():
        c = Configurator()
        encoded = c._toxbit('ABC', digitalphaencoding=False)
        decoded = c._fromxbit(encoded, digitalphaencoding=False)

        expected = bytes([ord('A') & 0x3f,
                          ord('B') & 0x3f,
                          ord('C') & 0x3f])
        assert decoded == expected

    @staticmethod
    def test_toxbit_does_not_modify_string():
        c = Configurator()
        s = 'ABC'
        c._toxbit(s)
        assert s == 'ABC'

    @staticmethod
    def test_toxbit_does_not_modify_bytearray():
        c = Configurator()
        data = bytearray(b'ABC')
        original = data[:]
        c._toxbit(data)
        assert data == original
