import pytest

from src.main import Configurator


class TestConfigurator:

    #def test_init(self):
    #    pass

    def test_interval(self, config):
        config.set('interval', 300)
        assert config.get('interval') == 300

    def test_mmsi(self, config):
        config.set('mmsi', 123)
        assert config.get('mmsi') == 123

    def test_call_sign_6(self, config):
        config.set('call_sign', 'AB1234')
        assert config.get('call_sign') == 'AB1234'

    def test_call_sign_7(self, config):
        config.set('call_sign', 'AB12345')
        assert config.get('call_sign') == 'AB12345'

    def test_ais_ref_roundtrip(self, populated_config):
        ref = populated_config.get('ais_ref')
        assert ref['bow'] == 69
        assert ref['stern'] == 10

    def test_raw_bytes(self, populated_config):
        data = populated_config._config
        assert data[0] == 2  # interval encoding example
