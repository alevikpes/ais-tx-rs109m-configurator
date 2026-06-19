from src.fields import (
    UIntField,
    AsciiField,
    Ais6BitField,
    VendorIdField,
    PackedBitsField,
    AISReferenceField,
)


FIELD_TYPES = {
    'uint': UIntField,
    'ascii': AsciiField,
    'ais6bit': Ais6BitField,
    'vendor_id': VendorIdField,
    'packed_bits': PackedBitsField,
    'ais_ref': AISReferenceField,
}
