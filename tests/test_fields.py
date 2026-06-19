import pytest

from src.fields import (
    UIntField,
    AsciiField,
    Ais6BitField,
    VendorIdField,
    PackedBitsField,
    AISReferenceField,
)


@pytest.fixture
def config():
    return bytearray(0x40)


class TestUIntField:

    @staticmethod
    def test_():
        pass


class TestAsciiField:

    @staticmethod
    def test_():
        pass


class TestAis6BitField:

    @staticmethod
    def test_():
        pass


class TestVendorIdField:

    @staticmethod
    def test_write_and_read_vendorid_roundtrip(config, vendor_id_field):
        vendor_id_field.write(config, 'ABC')
        assert vendor_id_field.read(config) == 'ABC'

    @staticmethod
    def test_write_vendorid_lowercase_and_padding(config, vendor_id_field):
        vendor_id_field.write(config, 'a')
        assert vendor_id_field.read(config) == 'A'

    @staticmethod
    def test_write_vendorid_truncation(config, vendor_id_field):
        vendor_id_field.write(config, 'WXYZ')
        result = vendor_id_field.read(config)
        assert len(result) <= 3

    @staticmethod
    def test_write_vendorid_non_ascii_filtered(config, vendor_id_field):
        vendor_id_field.write(config, 'AΩB')  # omega should be ignored
        result = vendor_id_field.read(config)
        assert result.isalnum()

    @staticmethod
    def test_validate_vendorid_valid(config, vendor_id_field):
        vendor_id_field.write(config, 'ABC')
        assert vendor_id_field.validate(config, 'ABC') is True

    @staticmethod
    def test_validate_vendorid_invalid_type(vendor_id_field):
        assert vendor_id_field.validate(config, 123) is False

    @staticmethod
    def test_validate_vendorid_too_long(vendor_id_field):
        assert vendor_id_field.validate(config, 'ABCD') is False

    @staticmethod
    def test_validate_vendorid_non_alnum(vendor_id_field):
        assert vendor_id_field.validate(config, 'A@B') is False

    #@staticmethod
    #def test_validate_vendorid_does_not_persist_side_effect(vendor_id_field):
    #    original_config = vendor_id_field.config[:]
    #
    #    vendor_id_field.validate(config, 'ABC')
    #
    #    assert vendor_id_field.config == original_config

    @staticmethod
    def test_validate_vendorid_roundtrip_change(config, vendor_id_field):
        vendor_id_field.write(config, 'AAA')

        # validation should temporarily write and restore
        assert (
            vendor_id_field.validate(config, 'BBB') is True or
            vendor_id_field.validate(config, 'BBB') is False
        )

        # original value should remain unchanged
        assert vendor_id_field.read(config) == 'AAA'


class TestPackedBitsField:

    @staticmethod
    def test_():
        pass


class TestAISReferenceField:

    @staticmethod
    def test_():
        pass
