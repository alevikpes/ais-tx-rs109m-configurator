from pathlib import Path

import pytest

from src.main import Configurator


@pytest.fixture
def default_config() -> Configurator:
    '''Return a fresh default configuration.'''
    return Configurator()


#@pytest.fixture
#def golden_config_bytes() -> bytes:
#    '''
#    Load a known-good RS-109 EEPROM dump.
#    '''
#
#    path = (
#        Path(__file__).parent
#        / 'fixtures'
#        / 'rs109_default.bin'
#    )
#
#    return path.read_bytes()
