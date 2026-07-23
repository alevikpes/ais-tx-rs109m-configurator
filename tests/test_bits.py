from rs109 import (
    _read_bits,
    _write_bits,
)


def test_read_single_byte():

    data = bytes([
        0b10101100,
    ])

    assert _read_bits(
        data,
        0,
        4,
    ) == 0b1100


def test_write_single_byte():

    data = bytearray([
        0,
    ])

    _write_bits(
        data,
        0,
        0b1010,
        4,
    )

    assert data[0] == 0b1010


def test_write_cross_byte_boundary():

    data = bytearray([
        0,
        0,
    ])

    _write_bits(
        data,
        6,
        0b111111,
        6,
    )

    assert _read_bits(
        data,
        6,
        6,
    ) == 0b111111


def test_write_preserves_other_bits():

    data = bytearray([
        0xff,
    ])

    _write_bits(
        data,
        2,
        0,
        3,
    )

    assert data[0] == 0b11100011
