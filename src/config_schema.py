"""Memory map.

Parameter  | Offset                         | Length (bytes)    | Comments
----------------------------------------------------------
interval   | 0                              | 1
mmsi       | 1–4                            | 4
ship_name  | 5–24                           | 20
ser_num    | 25–27 (packed with unit_model) | 3                 | some buoys report battery charge level here
unit_model | upper nibble of byte 27        | 0.5
vendor_id  | 28–30 (packed)                 | 3
ship_type  | 31                             | 1
call_sign  | 32–37                          | 6
ais2bow    | 38–39 (packed)                 | 2                 | distance AIS to bow (m); some buoys report battery voltage here
ais2stern  | 39–40 (packed)                 | 2                 | distance AIS to stern (m)
ais2port   | 40–41 (packed)                 | 2                 | distance AIS to port (m)
ais2star   | 41                             | 1                 | distance AIS to starboard (m)
"""


from src.fields import (
    UIntField,
    AsciiField,
    Ais6BitField,
    VendorIdField,
    PackedBitsField,
    AISReferenceField,
)


MEMORY_MAP = [
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
FIELD_TYPES = {
    'uint': UIntField,
    'ascii': AsciiField,
    'ais6bit': Ais6BitField,
    'vendor_id': VendorIdField,
    'packed_bits': PackedBitsField,
    'ais_ref': AISReferenceField,
}


def build_fields():
    fields = {}

    for name, offset, length, ftype in MEMORY_MAP:
        cls = FIELD_TYPES[ftype]

        # special constructor handling
        if ftype == 'packed_bits':
            fields[name] = cls(offset, 4, 4)
        else:
            fields[name] = cls(offset, length)

    return fields
