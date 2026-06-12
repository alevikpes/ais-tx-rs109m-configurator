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
    parser.add_argument('-u', '--unitmodel', help='AIS unit vendor model code')
    parser.add_argument(
        '-s',
        '--sernum',
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


class Configurator:
    #default_config = bytearray([
    #        0x04, 0x2d, 0xd2, 0x7f, 0x06, 0x31, 0x30, 0x39, 0x30, 0x34, 0x30, 0x31, 0x37, 0x33, 0x20, 0x20,
    #        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x01, 0x00, 0x00, 0xe0, 0x24, 0x01, 0x00,
    #        0x35, 0x3d, 0xcb, 0xf1, 0x23, 0x00, 0x08, 0xa0, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,

    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    #        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff
    #])
    default_len = 0x40

    def __init__(self, config):
           #self._config = config if config else self.default_config
           self._config = config

    def __repr__(self):
        return '[ 0x' + self._config.hex('#').replace('#',', 0x') + ' ]'

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, val):
        # TODO: implement differently, as setting config as slices config[34:38] might be convenient
        #clen = 0xff if (len(val) > 0xff) else len(val)
        #self._config = bytearray(val[0:clen] + self.default_config[clen:])
        self._config = bytearray(val) + bytearray(0x40-len(val))

    @property
    def mmsi(self):
        return (
            self._config[1] + 
            (self._config[2] << 8) + 
            (self._config[3] << 16) + 
            ((self._config[4] & 0xff) << 24)
        )

    @mmsi.setter
    def mmsi(self, val):
        mmsi = int(val)
        self._config[1] = mmsi & 0xff
        self._config[2] = (mmsi >> 8) & 0xff
        self._config[3] = (mmsi >> 16) & 0xff
        self._config[4] = (mmsi >> 24) & 0xff

    @property
    def ship_name(self):
        return bytes(self._config[5:25]).decode('ascii').strip()

    @ship_name.setter
    def ship_name(self, val):
        # TODO: check for invalid chars, this one is incomplete
        safe_name = val.encode('ascii', 'ignore').decode().upper().ljust(20, ' ').encode('ascii')
        self._config[5:25] = safe_name

    @property
    def interval(self):
        """Transmitting interval."""
        return self._config[0] * 30

    @interval.setter
    def interval(self, val):
        seconds = int(val)
        if seconds > 600:
            seconds = 600
        elif seconds < 30:
            seconds = 30

        self._config[0] = seconds // 30

    @property
    def ship_type(self):
        """Ship type."""
        return int(self._config[31])

    @ship_type.setter
    def ship_type(self, val):
        self._config[31] = int(val) & 0xff

    @property
    def vendor_id(self):
        vid = [
            (self._config[29] >> 4) | ((self._config[30]  & 0x03) << 4) | 0x40,
            (self._config[28] >> 6) | ((self._config[29] & 0x07) << 2) | 0x40,
            (self._config[28] & 0x3f) | 0x40
        ]
        return  ''.join(c if c.isalnum() else '' for c in bytes(vid).decode())

    @vendor_id.setter
    def vendor_id(self, val):
        # TODO: check for invalid chars, this one is incomplete
        safe_vid = val.encode('ascii', 'ignore').decode().upper().ljust(3, '\x00')[:3].encode('ascii')
        print(safe_vid)
        self._config[28] = (safe_vid[2] & 0x3f) | ((safe_vid[1] << 6 ) & 0xff)
        self._config[29] = ((safe_vid[1] >> 2) & 0x0f) | ((safe_vid[0] << 4) & 0xff)
        self._config[30] = (self._config[30] & ~0x0f) | ((safe_vid[0] & 0x3f) >> 4)

    def get_unitmodel(self):
        unitmodel = self._config[27] >> 4
        return unitmodel

    def set_unitmodel(self, unitmodel):
        unitmodel = int(unitmodel)
        if unitmodel < 0 or unitmodel > 15:
            raise ValueError('UnitModel must be 0 < unitmodel <= 15')
        self._config[27] = (self._config[27] & 0xf0) | ((int(unitmodel) & 0x0f) << 4)

    unitmodel = property(get_unitmodel, set_unitmodel)

    def get_sernum(self):
        sernum = self._config[25] + (self._config[26] << 8) + ((self._config[27] & 0x0f) << 16)
        return sernum

    def set_sernum(self, sernum):
        sernum = int(sernum)
        if sernum < 0 or sernum > ((1 << 20) - 1):
            raise ValueError('UnitSernum must be 0 <= sernum <= ', ((1 << 20) - 1))

        self._config[25] = sernum & 0xff
        self._config[26] = (sernum >> 8) & 0xff
        self._config[27] = (self._config[27] & 0xf0) | ((sernum >> 16) & 0x0f)

    sernum = property(get_sernum, set_sernum)

    def _fromxbit(ba, x=6, digitalphaencoding=True):
        if ((x < 1) or (x > 7)):
            raise ValueError('BitLen must be between 1 and 7')

        if len(ba) < 1:
            raise ValueError('Must supply non-empty array')

        n = len(ba) * 8 // x
        b = bytearray([0 for i in range(n)])

        for i in range(n):
            pos = i * x // 8
            shift = i * x % 8

            b[i] = (ba[pos] >> shift) & ((1 << x) - 1)
            remaining = shift + x - 8
            if remaining > 0:
                b[i] |= (ba[pos + 1] << (8 -  shift)) & ((1 << x) - 1)

            if digitalphaencoding and (b[i] & 0x20) != 0x20 and b[i] != 0:
                # not a digit, is alpha
                b[i] = (b[i] & 0x1f) | 0x40

        return b

    @property
    def call_sign(self):
        # TODO: check if it is 32:37 or 32:38
        # derek@conniffe.com - changed to 32:38 to
        # support valid 7 digit callsigns
        s = self._fromxbit(self._config[32:38], 6).decode('ascii')[::-1]
        return ''.join(c if c.isalnum() else '' for c in s)

    def _toxbit(ba, x=6, digitalphaencoding=True):
        if ((x < 1) or (x > 7)):
            raise ValueError('BitLen must be between 1 and 7')

        if len(ba) < 1:
            return [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]

        if digitalphaencoding:
           ba = bytearray(ba.encode('ascii', 'ignore').decode().upper().encode('ascii'))

        n = len(ba) * x // 8
        if (len(ba) * x % 8) > 0:
            n += 1

        if n == 0:
            n = 1

        b = bytearray([0 for i in range(n)])

        for i in range(len(ba)):
            pos = i * x // 8
            shift = i * x % 8

            ba[i] = ba[i] & ((1 << x) - 1)

            b[pos] |= (ba[i] << shift) & 0xff
            remaining = shift + x - 8
            # print(ba[i], ' i=', i, ' pos=', pos, ' shift=', shift, ' remaining=', remaining)
            if remaining > 0:
                b[pos+1] |= (ba[i] >> (8 - shift))

        return b

    @call_sign.setter
    def call_sign(self, cs):
        safe_cs = ''.join(c if c.isalnum() else '' for c in cs)
        # derek@conniffe.com - changed to 32:38 to
        # support valid 7 digit callsigns
        self._config[32:38] = self._toxbit(safe_cs[::-1])

    def get_refa(self):
        return (self._config[39] >> 5) | ((self._config[38] & ((1 << 6) - 1)) << 3)

    def set_refa(self, a):
        if int(a) > (1 << 9):
            raise ValueError('Reference a must be <= 511')
        if int(a) < 0:
            raise ValueError('Reference a must be >= 0')
        self._config[39] = (self._config[39] & ((1 << 5) - 1)) | (((int(a) & ((1 << 6) - 1)) << 5) & 0xff)
        self._config[38] = (self._config[38] & ~((1 << 4) - 1)) | ((int(a) & ((1<<9) - 1)) >> 3)

    refa = property(get_refa, set_refa)

    def get_refb(self):
        return (self._config[40] >> 4) | ((self._config[39] & ((1<<5) -1)) << 4)

    def set_refb(self, b):
        if int(b) > (1<<9):
            raise ValueError('Reference b must be <= 511')
        if int(b) < 0:
            raise ValueError('Reference b must be >= 0')
        self._config[40] = (self._config[40] & ((1<<4) -1)) | (((int(b) & ((1<<6) -1)) << 4) & 0xff)
        self._config[39] = (self._config[39] & ~((1<<5) -1)) | ((int(b) & ((1<<9) -1)) >> 4)

    refb = property(get_refb, set_refb)

    def get_refc(self):
        return (self._config[41] >> 6) | ((self._config[40] & ((1<<4) -1)) << 2)

    def set_refc(self, c):
        if int(c) > (1<<6):
            raise ValueError('Reference c must be <= 63')

        if int(c) < 0:
            raise ValueError('Reference c must be >= 0')

        self._config[41] = (self._config[41] & ((1<<6) -1)) | (((int(c) & ((1<<6) -1)) << 6) & 0xff)
        self._config[40] = (self._config[40] & ~((1<<4) -1)) | ((int(c) & ((1<<6) -1)) >> 2)

    refc = property(get_refc, set_refc)

    def get_refd(self):
        return self._config[41] & ((1<<6) -1)

    def set_refd(self, d):
        if int(d) > (1<<6):
            raise ValueError('Reference d must be <= 63')
        if int(d) < 0:
            raise ValueError('Reference d must be >= 0')
        self._config[41] = (self._config[41] & ~((1<<6) -1)) | (int(d) & ((1<<6) -1))

    refd = property(get_refd, set_refd)

if __name__ == '__main__':

    max_retries = 3

    def serial_cmd(ser, tx_bytes, expected_prefix, read_extra=0):
        print(f'Writing data: {tx_bytes.decode("ascii", errors="ignore").strip()}')
        # Send command and check response, with retries. Returns full response bytes.
        for attempt in range(max_retries):
            ser.reset_input_buffer()
            ser.write(tx_bytes)
            r = ser.read(len(expected_prefix))
            print(f'Expected prefix: {r.decode("ascii", errors="ignore").strip()}')
            if r == expected_prefix:
                if read_extra > 0:
                    re = ser.read(read_extra)
                    print(f'Read extra: {re.decode("ascii", errors="ignore").strip()}')
                    return r + re

                return r

        return None

    args = cli_parser()

    c = Configurator()

    num_bytes = c.default_len
    if args.extended:
        num_bytes = 0xff

    ser = None

    if args.device != None:
        ser = serial.Serial()
        ser.port = args.device

        ser.baudrate = 115200
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE

        ser.timeout = 1
        ser.write_timeout = 3

        ser.open()

        # RTS toggle to wake/reset the device (this is usually hard-wired, but we do that here to follow manufacturer specs)
        ser.rts = False
        # import time; time.sleep(0.05)
        ser.rts = True

        # try read and timeout seems to make more reliable connection
        ser.read(0xffff)
        ser.timeout = 3

        password_maxlen = 6
        password_prepared = PASSWORD_DEFAULT.encode()[:password_maxlen]

        if args.password != None:
            password = args.password

            if not re.match('^[0-9]{0,'+str(password_maxlen)+'}$', password):
                print('Password: incorrect format, should match [0-9]{0,'+str(password_maxlen)+'}')
                exit(1)

            password_prepared = (password.encode() + PASSWORD_DEFAULT.encode())[:password_maxlen]
            auth_cmd = bytes([0x59, 0x01, 0x42, password_maxlen]) + password_prepared
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

    if args.unitmodel != None:
        c.unitmodel = args.unitmodel

    if args.sernum!= None:
        c.sernum= args.sernum

    if args.refa != None:
        c.refa = int(args.refa)

    if args.refb != None:
        c.refb = int(args.refb)

    if args.refc != None:
        c.refc = int(args.refc)

    if args.refd != None:
        c.refd = int(args.refd)

    print(f'\tMMSI: {"mmsi": c.mmsi}')
    print(f'\tShip name: {c.ship_name}')
    print(f'\tTX interval (s): {c.interval}')
    print(f'\tShip type: {c.ship_type}')
    print(f'\tCallsign: {c.call_sign}')
    print(f'\tVendorID: {c.vendor_id}')
    print(f'\tUnitModel: {c.unitmodel}')
    print(f'\tUnitSerial: {c.sernum} (may be battery level {c.sernum}% on some devices)')
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

