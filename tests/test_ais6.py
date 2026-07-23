from rs109 import (
    encode_ais6,
    decode_ais6,
)


def test_ais6_round_trip():

    original = 'TEST123'

    encoded = encode_ais6(
        original
    )

    decoded = decode_ais6(
        encoded
    )

    assert (
        bytes(decoded)
        .decode('ascii')
        .strip()
        ==
        original
    )


def test_ais6_uppercase_conversion():

    encoded = encode_ais6(
        'abc'
    )

    decoded = decode_ais6(
        encoded
    )

    assert (
        bytes(decoded)
        .decode('ascii')
        ==
        'ABC'
    )


def test_empty_encode():

    assert encode_ais6(
        ''
    ) == bytearray(
        b'\xff' * 6
    )


def test_invalid_bit_width():

    try:
        encode_ais6(
            'ABC',
            8,
        )

    except ValueError as exc:

        assert (
            'bits must be between'
            in str(exc)
        )

    else:
        assert False
