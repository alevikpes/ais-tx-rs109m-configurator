import pytest

from src.configurator import Configurator


@pytest.fixture
def config():
    """
    Returns a fresh Configurator with default device state.
    Each test gets an isolated instance.
    """
    return Configurator()


@pytest.fixture
def populated_config():
    c = Configurator()

    c.set('mmsi', 123456789)
    c.set('ship_name', 'TEST SHIP')
    c.set('interval', 60)
    c.set('ship_type', 36)
    c.set('call_sign', 'ABC123')
    c.set('vendor_id', 'BYY')
    c.set('unit_model', 3)
    c.set('ais_ref', {
        'bow': 69,
        'stern': 10,
        'port': 2,
        'starboard': 2,
    })

    return c


@pytest.fixture
def raw_config():
    """
    Returns raw bytearray for low-level validation tests.
    """
    return bytearray(0x40)


@pytest.fixture
def config_with_map():
    return Configurator(memory_map=MEMORY_MAP)
