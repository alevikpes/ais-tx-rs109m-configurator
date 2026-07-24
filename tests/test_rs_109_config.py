from main import Configurator


def test_mmsi(default_config):
    default_config.mmsi = 123456789
    assert default_config.mmsi == 123456789


def test_name(default_config):
    default_config.name = 'Test Boat'
    assert default_config.name == 'TEST BOAT'


def test_name_truncation(default_config):

    default_config.name = (
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    )

    assert len(
        default_config.name
    ) == 20


def test_interval_limits(default_config):

    default_config.interval = 10

    assert (
        default_config.interval
        ==
        30
    )

    default_config.interval = 9999

    assert (
        default_config.interval
        ==
        600
    )


def test_callsign(default_config):

    default_config.callsign = 'PA1234'

    assert (
        default_config.callsign
        ==
        'PA1234'
    )


def test_vendor_id(default_config):

    default_config.vendorid = 'ABC'

    assert (
        default_config.vendorid
        ==
        'ABC'
    )


def test_serial_number(default_config):

    default_config.sernum = 0xABCDE

    assert (
        default_config.sernum
        ==
        0xABCDE
    )


def test_unit_model(default_config):

    default_config.unitmodel = 7

    assert (
        default_config.unitmodel
        ==
        7
    )


import pytest


@pytest.mark.parametrize(
    'field,value',
    [
        ('refa', 511),
        ('refb', 511),
        ('refc', 63),
        ('refd', 63),
    ],
)
def test_reference_fields(
    default_config,
    field,
    value,
):

    setattr(
        default_config,
        field,
        value,
    )

    assert getattr(
        default_config,
        field,
    ) == value




def test_default_configuration():

    config = RS109Config()

    assert (
        config.config[:5]
        ==
        bytearray([
            0x04,
            0x2d,
            0xd2,
            0x7f,
            0x06,
        ])
    )

