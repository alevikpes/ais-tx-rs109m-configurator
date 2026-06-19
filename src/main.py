import re

import serial

import src.fields as fields_classes
from src.args_parser import cli_parser
from src.field_builder import build_fields
from src.memory_map import MEMORY_MAP


PASSWORD_DEFAULT = '000000'
#FIELDS = {
#    'interval': fields_classes.UIntField(0, 1),
#    'mmsi': fields_classes.UIntField(1, 4),
#    'ship_name': fields_classes.AsciiField(5, 20),
#    'ser_num': fields_classes.UIntField(25, 3),
#    'unit_model': fields_classes.PackedBitsField(27, 4, 4),
#    'vendor_id': fields_classes.VendorIdField(28, 3),
#    'ship_type': fields_classes.UIntField(31, 1),
#    'call_sign': fields_classes.Ais6BitField(32, 6),
#    'ais2bow': ,
#    'ais2stern': ,
#    'ais2port': ,
#    'ais2star': ,
#    #'ais_ref': fields.AISReferenceField(38, 4),
#}


class Configurator:

    """Configurator.

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

    def __init__(self):
        self._config = bytearray(0x40)
        self.fields = build_fields(MEMORY_MAP)

    def get(self, name):
        field = self.fields.get(name)
        field.read(self._config)
        return field

    def set(self, name, value):
        field = self.fields.get(name)
        field.validate(value)
        field.write(self._config, value)

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


if __name__ == '__main__':

    args = cli_parser()

    c = Configurator(args)

    num_bytes = c.default_len
    if args.extended:
        num_bytes = 0xff

    ser = None

    with serial.Serial(
        '/dev/ttyUSB0',
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
        write_timeout=3,
    ) as ser:
        # RTS toggle to wake/reset the device (this is usually hard-wired,
        # but we do that here to follow manufacturer specs)
        ser.rts = False
        # import time; time.sleep(0.05)
        ser.rts = True

        # try read and timeout seems to make more reliable connection
        ser.read(0xffff)
        #ser.timeout = 3

        password_maxlen = 6
        password_prepared = PASSWORD_DEFAULT.encode()[:password_maxlen]

        if args.password != None:
            password = args.password
            if not re.match('^[0-9]{0,'+str(password_maxlen)+'}$', password):
                print('Password: incorrect format, should match [0-9]{0,'+str(password_maxlen)+'}')
                exit(1)

            password_prepared = (
                password.encode() + PASSWORD_DEFAULT.encode()
            )[:password_maxlen]
            auth_cmd = (
                bytes([0x59, 0x01, 0x42, password_maxlen]) +
                password_prepared
            )
        else:
            # This seems to work even with a password set
            auth_cmd = bytes([0x59, 0x01, 0x42, 0x00])

        r = serial_cmd(ser, auth_cmd, b'\x95\x20')
        if r is None and args.password != None:
            # zero-length password seems to work even with a password set on some devices
            r = serial_cmd(ser, bytes([0x59, 0x01, 0x42, 0x00]), b'\x95\x20')

        if r is None:
            print('Could not initialize with password.')
            exit(1)

        if args.clearpass:
            r = serial_cmd(ser, bytes([0x59, 0x02, 0x42, password_maxlen]) + password_prepared, b'\x95\x20')
            if r is None:
                print('Clear password failed.')
                exit(1)

            print('Password cleared successfully!')
            exit(0)

        if args.setpass != None:
            newpass = args.setpass
            if not re.match('^[0-9]{1,'+str(password_maxlen)+'}$', newpass):
                print('New password: incorrect format, should match [0-9]{1,'+str(password_maxlen)+'}')
                exit(1)

            newpass_prepared = (newpass.encode() + PASSWORD_DEFAULT.encode())[:password_maxlen]
            r = serial_cmd(ser, bytes([0x59, 0x03, 0x42, password_maxlen]) + password_prepared + newpass_prepared, b'\x95\x20')
            if r is None:
                print('Set password failed.')
                exit(1)

            print('Password set successfully!')
            exit(0)

        if args.noread == False:
            r = serial_cmd(ser, bytes([0x51, num_bytes]), bytes([0x25, num_bytes]), read_extra=num_bytes)
            if r is None or len(r) != 2 + num_bytes:
                print('Could not read config from device')
                exit(1)

            c.config = r[2:]
    else:
        print('Operating on default config:')
        print()

    if args.mmsi != None:
        c.mmsi = args.mmsi

    if args.ship_name != None:
        c.ship_name = args.ship_name

    if args.interval != None:
        c.interval = args.interval

    if args.ship_type != None:
        c.ship_type = args.ship_type

    if args.call_sign != None:
        c.call_sign = args.call_sign

    if args.vendor_id!= None:
        c.vendor_id = args.vendor_id

    if args.unit_model != None:
        c.unit_model = args.unit_model

    if args.ser_num!= None:
        c.ser_num= args.ser_num

    if args.refa != None:
        c.refa = int(args.refa)

    if args.refb != None:
        c.refb = int(args.refb)

    if args.refc != None:
        c.refc = int(args.refc)

    if args.refd != None:
        c.refd = int(args.refd)

    print(f'\tMMSI: {c.mmsi}')
    print(f'\tShip name: {c.ship_name}')
    print(f'\tTX interval (s): {c.interval}')
    print(f'\tShip type: {c.ship_type}')
    print(f'\tCallsign: {c.call_sign}')
    print(f'\tVendorID: {c.vendor_id}')
    print(f'\tUnitModel: {c.unit_model}')
    print(f'\tUnitSerial: {c.ser_num} (may be battery level {c.ser_num}% on some devices)')
    print(f'\tReference point A (m): {c.refa} (may be battery voltage {(c.refa/10.0):.1f}V on some devices)')
    print(f'\tReference point B (m): {c.refb}')
    print(f'\tReference point C (m): {c.refc}')
    print(f'\tReference point D (m): {c.refd}')
    print()
    #print('[ 0x' + c.config[:num_bytes].hex('#').replace('#',', 0x') + ' ]')

    if args.device != None and args.write:
        write_cmd = bytes([0x55, num_bytes]) + c.config[:num_bytes]
        r = serial_cmd(ser, write_cmd, bytes([0x75, num_bytes]))
        #print('Read-back matches:', r[2:]==c.config[:num_bytes])
        if r is None:
            print('Write failed')
            exit(1)
        else:
            print('Config written successfully!')
    else:
        if args.write:
            print('Must supply serial device with -d option.')
            exit(1)

