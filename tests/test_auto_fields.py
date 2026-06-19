import random

import pytest

from src.config_schema import FIELD_TYPES, MEMORY_MAP, build_fields
#from src.configurator import Configurator


MEMORY_MAP_TEST = [
    ('interval', 0, 1, 'uint'),
    ('mmsi', 1, 4, 'uint'),
    ('ship_name', 5, 20, 'ascii'),
    ('ser_num', 25, 3, 'uint'),
    ('unit_model', 27, 1, 'packed_bits'),  # packed nibble inside byte 27
    ('vendor_id', 28, 3, 'vendor_id'),
    ('ship_type', 31, 1, 'uint'),
    ('call_sign', 32, 6, 'ais6bit'),
    ('ais_ref', 38, 4, 'ais_ref'),  # packed bitfield block
]


def get_test_values():
    return {
        'uint': [0, 1, 10, 255],
        'ascii': ['A', 'TEST', 'HELLO123'],
        'ais6bit': ['AB1234', 'CALL123'],
        'vendor_id': ['BYY', 'ABC'],
        'packed_bits': [0, 5, 15],
        'ais_ref': [
            {'bow': 1, 'stern': 2, 'port': 3, 'starboard': 4},
            {'bow': 255, 'stern': 0, 'port': 10, 'starboard': 63},
        ],
    }


@pytest.mark.parametrize('name,offset,length,ftype', MEMORY_MAP_TEST)
def test_roundtrip_all_fields(config, name, offset, length, ftype):
    c = config
    fields = build_fields()

    field = fields[name]

    values = get_test_values()[ftype]

    for value in values:
        c.set(name, value)
        result = c.get(name)

        assert result == value


@pytest.mark.parametrize('name,offset,length,ftype', MEMORY_MAP)
def test_field_isolation(config, name, offset, length, ftype):
    c = config

    original = c._config[:]

    c.set(name, get_test_values()[ftype][0])

    for i in range(len(original)):
        if offset <= i < offset + length:
            continue

        assert c._config[i] == original[i]



@pytest.mark.parametrize('name,offset,length,ftype', MEMORY_MAP)
def test_fuzz_fields(config, name, offset, length, ftype):
    c = config

    values = get_test_values()[ftype]

    for _ in range(20):
        value = random.choice(values)
        c.set(name, value)
        assert c.get(name) == value


def test_uint_overflow_clamps(config):
    c = config

    c.set('unit_model', 9999)
    assert c.get('unit_model') <= 15
