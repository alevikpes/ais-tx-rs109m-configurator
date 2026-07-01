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


import re

from fields import (
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


class Configurator:
    """Configurator."""

    default_len = 0x40

    def __init__(self, args):
        self.args = args
        self._config = bytearray(self.default_len)
        self.fields = build_fields()

    def get_field(self, name):
        field = self.fields.get(name)
        return field.read(self._config)

    def set_field(self, name, value):
        field = self.fields.get(name)
        field.validate(value)
        field.write(self._config, value)

    def get(self):
        data = []
        for arg in vars(self.args):
            data.append({arg: self.get_field(arg)})

        return data

    def set(self):
        for k, v in vars(self.args).items():
            self.set_field(k, v)

    def serial_cmd(
        self,
        ser,
        tx_bytes,
        expected_prefix,
        read_extra=0,
        max_retries=3,
    ):
        """Method for sending a command to the device."""
        print(
            'Sending command: '
            f'{tx_bytes.decode('ascii', errors='ignore').strip()}'
        )
        # Send command and check response, with retries.
        # Returns full response bytes.
        for attempt in range(max_retries):
            ser.reset_input_buffer()
            ser.write(tx_bytes)
            r = ser.read(len(expected_prefix))
            print(
                'Expected prefix: '
                f'{r.decode('ascii', errors='ignore').strip()}',
            )
            if len(r) == len(expected_prefix) and r == expected_prefix:
                if read_extra > 0:
                    re = ser.read(read_extra)
                    print(f'Read extra: {re.decode('ascii', errors='ignore').strip()}')
                    return r + re

                return r

        return None
