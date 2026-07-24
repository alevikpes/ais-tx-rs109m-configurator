import serial

from cli_parser import cli_parser
from configurator import Configurator


NAME_OFFSET = 5
NAME_LENGTH = 20

CALLSIGN_START = 32
CALLSIGN_END = 38

UNITMODEL_OFFSET = 27

SHIPTYPE_OFFSET = 31

PASSWORD_DEFAULT = '000000'


def serial_cmd(ser, tx_bytes, expected_prefix, read_extra=0, max_retries=3):
    # Send command and check response, with retries. Returns full response bytes.
    for attempt in range(max_retries):
        ser.reset_input_buffer()
        ser.write(tx_bytes)
        r = ser.read(len(expected_prefix))
        if r == expected_prefix:
            if read_extra > 0:
                return r + ser.read(read_extra)

            return r

    return None


def fromxbit(ba, x=6, digitalphaencoding=True):
    if ((x < 1) or (x > 7)):
        raise ValueError('BitLen must between 1 and 7')

    if len(ba) < 1:
        raise ValueError('Must supply non-empty array')

    n = len(ba) * 8 // x
    b = bytearray([0 for i in range(n)])

    for i in range(n):
        pos = i * x // 8
        shift = i * x % 8

        b[i] = (ba[pos] >> shift) & ((1 << x) -1)
        remaining = shift + x - 8
        if remaining > 0:
            b[i] |= (ba[pos + 1] << (8 -  shift)) & ((1 << x) -1)
        if digitalphaencoding and (b[i] & 0x20) != 0x20 and b[i] != 0:
            # not a digit, is alpha
            b[i] = (b[i] & 0x1f) | 0x40

    return b

def toxbit(ba, x=6, digitalphaencoding=True):
    if ((x < 1) or (x > 7)):
        raise ValueError('BitLen must between 1 and 7')

    if len(ba) < 1:
        return [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]

    if digitalphaencoding:
       ba = bytearray(
           ba.encode('ascii', 'ignore').decode().upper().encode('ascii')
       )

    n = len(ba) * x // 8
    if (len(ba) * x % 8) > 0:
        n += 1

    if n == 0:
        n = 1

    b = bytearray([0 for i in range(n)])

    for i in range(len(ba)):
        pos = i * x // 8
        shift = i * x % 8

        ba[i] = ba[i] & ((1 << x) -1)

        b[pos] |= (ba[i] << shift) & 0xff
        remaining = shift + x - 8
        # print(ba[i], " i=", i, " pos=", pos, " shift=", shift, " remaining=", remaining)
        if remaining > 0:
            b[pos +1] |= (ba[i] >> (8 - shift))

    return b


if __name__ == '__main__':

    args = cli_parser()

    if not args.device:
        print('Operating on default config:\n')

    with serial.Serial(
        port=args.device,
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

        password_maxlen = 6
        password_prepared = PASSWORD_DEFAULT.encode()[:password_maxlen]

        if args.password:
            password = args.password
            if len(password) != password_maxlen or not password.isdigit():
                raise ValueError(
                    'Password must be an integer of '
                    f'{password_maxlen} digit length.'
                )

            password_prepared = (
                password.encode() + PASSWORD_DEFAULT.encode()
            )[:password_maxlen]
            auth_cmd = bytes([0x59, 0x01, 0x42, password_maxlen]) \
                + password_prepared
        else:
            # This seems to work even with a password set
            auth_cmd = bytes([0x59, 0x01, 0x42, 0x00])

        r = serial_cmd(ser, auth_cmd, b'\x95\x20')
        if r is None and args.password is not None:
            # zero-length password seems to work even with
            # a password set on some devices
            r = serial_cmd(ser, bytes([0x59, 0x01, 0x42, 0x00]), b'\x95\x20')
        if r is None:
            print('Could not initialize with password.')
            exit(1)

        if args.clearpass:
            r = serial_cmd(
                ser,
                bytes([0x59, 0x02, 0x42, password_maxlen]) + password_prepared,
                b'\x95\x20',
            )
            if r is None:
                print('Clear password failed.')
                exit(1)

            print('Password cleared successfully!')
            exit(0)

        if args.setpass is not None:
            newpass = args.setpass
            if len(newpass) != password_maxlen or not newpass.isdigit():
                raise ValueError(
                    'Password must be an integer of '
                    f'{password_maxlen} digit length.'
                )

            newpass_prepared = (
                newpass.encode() + PASSWORD_DEFAULT.encode()
            )[:password_maxlen]
            r = serial_cmd(
                ser,
                bytes([0x59, 0x03, 0x42, password_maxlen]) \
                    + password_prepared \
                    + newpass_prepared,
                b'\x95\x20',
            )
            if r is None:
                print('Set password failed.')
                exit(1)

            print('Password set successfully!')
            exit(0)

        c = Configurator()
        num_bytes = c.default_len

        if args.extended:
            num_bytes = 0xff

        if args.noread == False:
            r = serial_cmd(
                ser,
                bytes([0x51, num_bytes]),
                bytes([0x25, num_bytes]),
                read_extra=num_bytes,
            )
            if r is None or len(r) != (2 + num_bytes):
                print('Could not read config from device')
                exit(1)

            c.config = r[2:]

        for name, val in vars(args).items():
            if val is not None:
                if name in ['ais2bow', 'ais2stern', 'ais2port', 'ais2star']:
                    setattr(c, name, int(val))
                else:
                    setattr(c, name, val)

        print(f'\tMMSI: {c.mmsi}')
        print(f'\tName: {c.ship_name}')
        print(f'\tTX interval (s): {c.interval}')
        print(f'\tShip type: {c.ship_type}')
        print(f'\tCall sign: {c.call_sign}')
        print(f'\tVendor ID: {c.vendor_id}')
        print(f'\tUnit model: {c.unit_model}')
        print(
            f'\tSerial number: {c.ser_num} '
            f'(may be battery charge level {c.ser_num}% on some buoys)'
        )
        print(
            f'\tDistance to bow (m): {c.ais2bow:d} '
            f'(may be battery voltage {c.ais2bow/10.00:.1f}V on some buoys)'
        )
        print(f'\tDistance to stern (m): {c.ais2stern}')
        print(f'\tDistance to port (m): {c.ais2port}')
        print(f'\tDistance to starboard (m): {c.ais2star}')
        print()
        print(f'[ 0x{c.config[:num_bytes].hex("#").replace("#", ", 0x")} ]')

        if args.write:
            write_cmd = bytes([0x55, num_bytes]) + c.config[:num_bytes]
            r = serial_cmd(ser, write_cmd, bytes([0x75, num_bytes]))
            if r is None:
                print('Write failed')
                exit(1)
            else:
                print('Config written successfully!')
                exit(0)
