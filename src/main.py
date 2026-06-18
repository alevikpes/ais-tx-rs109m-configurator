import argparse
import re

import serial


PASSWORD_DEFAULT = '000000'


def cli_parser():
    parser = argparse.ArgumentParser(
        description='RS-109M Net Locator AIS configurator.',
    )
    parser.add_argument(
        'device',
        help='[Required] Serial port where the device is connected (e.g. /dev/ttyUSB0).',
    )
    parser.add_argument('-m', '--mmsi', help='MMSI.')
    parser.add_argument('-n', '--ship-name', help='Ship name.')
    parser.add_argument(
        '-i',
        '--interval',
        help='Transmit interval in s [30..600].',
    )
    parser.add_argument(
        '-t',
        '--ship-type',
        help='Ship type, eg sail=36, pleasure craft=37.',
    )
    parser.add_argument('-c', '--call-sign', help='Call sign.')
    parser.add_argument(
        '-v',
        '--vendor-id',
        help='AIS unit vendor id (3 characters).',
    )
    parser.add_argument('-u', '--unit-model', help='AIS unit vendor model code')
    parser.add_argument(
        '-s',
        '--ser-num',
        help=(
            'AIS unit serial num '
            '(some devices report battery level %% here).'
        ),
    )
    parser.add_argument(
        '-A',
        '--refa',
        help=(
            'Reference A (distance AIS to bow (m); '
            'some buoys report battery voltage here)'
        ),
    )
    parser.add_argument(
        '-B',
        '--refb',
        help='Reference B (distance AIS to stern (m).',
    )
    parser.add_argument(
        '-C',
        '--refc',
        help='Reference C (distance AIS to port (m).',
    )
    parser.add_argument(
        '-D',
        '--refd',
        help='Reference D (distance AIS to starboard (m).',
    )
    parser.add_argument(
        '-P',
        '--password',
        help='Password to access Net Locator. Default is 000000.',
    )
    parser.add_argument(
        '--setpass',
        help='Set new password (use -P for current password).',
    )
    parser.add_argument(
        '--clearpass',
        help='Clear password (use -P for current password)',
        action='store_true',
    )
    parser.add_argument(
        '-E',
        '--extended',
        help='Operate on 0xff size config instead of default 0x40',
        action='store_true',
    )
    parser.add_argument(
        '-W',
        '--write',
        help='Write config to Net Locator',
        action='store_true',
    )
    parser.add_argument(
        '-R',
        '--noread',
        help='Do not read from Net Locator',
        action='store_true',
    )
    return parser.parse_args()


def serial_cmd(ser, tx_bytes, expected_prefix, read_extra=0, max_retries = 3):
    print(f'Writing data: {tx_bytes.decode('ascii', errors='ignore').strip()}')
    # Send command and check response, with retries. Returns full response bytes.
    for attempt in range(max_retries):
        ser.reset_input_buffer()
        ser.write(tx_bytes)
        r = ser.read(len(expected_prefix))
        print(f'Expected prefix: {r.decode('ascii', errors='ignore').strip()}')
        if len(r) == len(expected_prefix) and r == expected_prefix:
            if read_extra > 0:
                re = ser.read(read_extra)
                print(f'Read extra: {re.decode('ascii', errors='ignore').strip()}')
                return r + re

            return r

    return None


class Field:
    """Abstract class for fields."""

    def __init__(self, offset, length):
        self.offset = offset
        self.length = length

    def read(self, config):
        raise NotImplementedError

    def write(self, config, value):
        raise NotImplementedError


class UIntField(Field):
    """Unsigned little-endian integer."""

    def read(self, config):
        return int.from_bytes(
            config[self.offset:self.offset+self.length],
            byteorder='little'
        )

    def write(self, config, value):
        config[self.offset:self.offset+self.length] = (
            int(value).to_bytes(self.length, 'little')
        )


class AsciiField(Field):
    """Fixed length ASCII string."""

    def read(self, config):
        return bytes(
            config[self.offset:self.offset+self.length]
        ).decode('ascii', errors='ignore').rstrip()

    def write(self, config, value):
        data = value.encode('ascii', errors='ignore')
        config[self.offset:self.offset+self.length] = (
            data[:self.length].ljust(self.length, b' ')
        )


class Ais6BitField(Field):
    """AIS 6-bit encoded string."""

    def _fromxbit(self, ba, x=6):
        n = len(ba) * 8 // x
        result = bytearray()
        for i in range(n):
            pos = i * x // 8
            shift = i * x % 8
            val = (ba[pos] >> shift) & ((1 << x)-1)
            if shift + x > 8:
                val |= (ba[pos+1] << (8-shift)) & ((1 << x)-1)

            if val != 0 and not (val & 0x20):
                val |= 0x40

            result.append(val)

        return result

    def _toxbit(self, data, x=6):
        data = bytearray(
            data.encode('ascii', errors='ignore')
            .upper()
        )
        size = (len(data)*x + 7)//8
        result = bytearray(size)
        for i, value in enumerate(data):
            value &= (1 << x)-1
            pos = i*x//8
            shift = i*x%8
            result[pos] |= value << shift
            if shift+x > 8:
                result[pos+1] |= value >> (8-shift)

        return result

    def read(self, config):
        raw = config[self.offset:self.offset+self.length]
        return self._fromxbit(raw).decode('ascii').rstrip()

    def write(self, config, value):
        encoded = self._toxbit(value)
        config[self.offset:self.offset+self.length] = (
            encoded.ljust(self.length, b'\x00')
        )


class VendorIdField(Field):
    """AIS 3 character vendor ID."""

    def read(self, config):
        b0 = config[28]
        b1 = config[29]
        b2 = config[30]
        chars = [
            (b0 >> 4) | ((b1 & 0x03) << 4),
            (b1 >> 2) | ((b2 & 0x0f) << 6),
            b2 & 0x3f,
        ]
        return ''.join(chr(c + 0x40) for c in chars)

    def write(self, config, value):
        value = value.upper().ljust(3)[:3]
        data = [ord(c) - 0x40 for c in value]
        config[28] = data[2] | ((data[1] & 0x03) << 6)
        config[29] = ((data[1] >> 2) & 0x0f) | (data[0] << 4)
        config[30] = config[30] & 0xf0 | ((data[0] >> 4) & 0x0f)


class PackedBitsField(Field):
    """Generic bit-field."""

    def __init__(self, offset, shift, bits):
        super().__init__(offset, 1)
        self.shift = shift
        self.mask = (1 << bits)-1

    def read(self, config):
        return (config[self.offset] >> self.shift) & self.mask

    def write(self, config, value):
        config[self.offset] &= ~(self.mask << self.shift)

        config[self.offset] |= (int(value) & self.mask) << self.shift


FIELDS = {
    'interval': UIntField(0, 1),
    'mmsi': UIntField(1, 4),
    'ship_name': AsciiField(5, 20),
    'sernum': UIntField(25, 3),
    'unitmodel': PackedBitsField(27, 4, 4),
    'vendor_id': VendorIdField(28, 3),
    'ship_type': UIntField(31, 1),
    'call_sign': Ais6BitField(32, 6),
}


class Configurator:

    """Configurator.

    Parameter  | Offset                         | Length (bytes)
    ----------------------------------------------------------
    interval   | 0                              | 1
    mmsi       | 1–4                            | 4
    ship_name  | 5–24                           | 20
    ser_num    | 25–27 (packed with unitmodel)  | 3
    unit_model | upper nibble of byte 27        | 0.5
    vendor_id  | 28–30 (packed)                 | 3
    ship_type  | 31                             | 1
    call_sign  | 32–37                          | 6
    refa       | 38–39 (packed)                 | 2
    refb       | 39–40 (packed)                 | 2
    refc       | 40–41 (packed)                 | 2
    refd       | 41                             | 1
    """

    def __init__(self):
        self._config = bytearray(0x40)

    def get(self, name):
        return FIELDS[name].read(self._config)

    def set(self, name, value):
        FIELDS[name].write(self._config, value)


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
    #if args.device != None:
    #    ser = serial.Serial()
    #    ser.port = args.device

    #    ser.baudrate = 115200
    #    ser.bytesize = serial.EIGHTBITS
    #    ser.parity = serial.PARITY_NONE
    #    ser.stopbits = serial.STOPBITS_ONE

    #    ser.timeout = 1
    #    ser.write_timeout = 3

    #    ser.open()

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

