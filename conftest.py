import pytest

from src.config_schema import Configurator, build_fields
from src.fields import VendorIdField


@pytest.fixture
def configurator():
    """
    Returns a fresh Configurator with default device state.
    Each test gets an isolated instance.
    """
    return Configurator()


@pytest.fixture
def fields():
    return build_fields()


@pytest.fixture
def vendor_id_field():
    return VendorIdField(28, 3)


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
