import random

import pytest

from src.field_builder import MEMORY_MAP, build_fields
#from src.configurator import Configurator


def get_test_values():
    return {
        'uint': [0, 1, 10, 255],
        'ascii': ['A', 'TEST', 'HELLO123'],
        'ais6bit': ['ABC', 'CALL123'],
        'vendor_id': ['BYY', 'ABC'],
        'packed_bits': [0, 5, 15],
        'ais_ref': [
            {'bow': 1, 'stern': 2, 'port': 3, 'starboard': 4},
            {'bow': 255, 'stern': 0, 'port': 10, 'starboard': 63},
        ],
    }


@pytest.mark.parametrize('name,offset,length,ftype', MEMORY_MAP)
def test_roundtrip_all_fields(config, name, offset, length, ftype):
    c = config
    fields = build_fields(MEMORY_MAP)

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
