from pathlib import Path

import pytest

from rs109 import RS109Config


@pytest.fixture
def default_config() -> RS109Config:
    '''
    Return a fresh default configuration.
    '''

    return RS109Config()


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
