from enum import IntEnum
from functools import lru_cache
from collections.abc import Buffer


@lru_cache(maxsize=None)
def _bit_mask(width: int) -> int:
    '''Return a mask containing ``width`` bits.

    Results are cached because the same field sizes are used repeatedly.
    '''
    if not 1 <= width <= 32:
        raise ValueError('bit width must be between 1 and 32')

    return (1 << width) - 1


def _read_bits(data: Buffer, bit_offset: int, width: int) -> int:
    '''Read ``width`` bits starting at ``bit_offset`` from packed bytes.

    Bits are stored least-significant-bit first, matching the RS-109
    configuration format.
    '''
    if width < 1:
        raise ValueError('width must be positive')

    byte_index = bit_offset // 8
    shift = bit_offset % 8

    value = data[byte_index] >> shift

    bits_read = 8 - shift

    if bits_read < width:
        value |= data[byte_index + 1] << bits_read

    return value & _bit_mask(width)


def _write_bits(
    data: bytearray,
    bit_offset: int,
    value: int,
    width: int,
) -> None:
    '''Write ``width`` bits starting at ``bit_offset`` into packed bytes.

    Existing unrelated bits are preserved.
    '''
    if width < 1:
        raise ValueError('width must be positive')

    mask = _bit_mask(width)

    value &= mask

    byte_index = bit_offset // 8
    shift = bit_offset % 8

    first_bits = min(width, 8 - shift)

    first_mask = ((1 << first_bits) - 1) << shift

    data[byte_index] &= ~first_mask
    data[byte_index] |= (value << shift) & first_mask

    remaining = width - first_bits

    if remaining:
        second_mask = (1 << remaining) - 1

        data[byte_index + 1] &= ~second_mask
        data[byte_index + 1] |= value >> first_bits


def _read_field(data: Buffer, offset: int, width: int) -> int:
    '''Read a field specified by byte offset and bit width.'''
    return _read_bits(data, offset * 8, width)


def _write_field(data: bytearray, offset: int, width: int, value: int) -> None:
    '''Write a field specified by byte offset and bit width.'''
    _write_bits(data, offset * 8, value, width)


def decode_ais6(
    data: Buffer,
    bits: int=6,
    digitalphaencoding: bool=True,
) -> bytearray:
    '''Decode packed AIS 6-bit characters.'''
    if not 1 <= bits <= 7:
        raise ValueError('bits must be between 1 and 7')

    data = memoryview(data)

    if not data:
        raise ValueError('data must not be empty')

    count = len(data) * 8 // bits
    result = bytearray(count)

    for index in range(count):
        value = _read_bits(data, index * bits, bits)

        if digitalphaencoding and value != 0 and value < 32:
            value |= 0x40

        result[index] = value

    return result


def encode_ais6(
    data: str | bytes | bytearray,
    bits: int=6,
    digitalphaencoding: bool=True,
) -> bytearray:
    '''Encode AIS 6-bit characters into packed bytes.'''
    if not 1 <= bits <= 7:
        raise ValueError('bits must be between 1 and 7')

    if not data:
        return bytearray(b'\xff' * 6)

    if isinstance(data, str):
        data = data.encode('ascii', 'ignore')
    else:
        data = bytes(data)

    if digitalphaencoding:
        data = data.upper()

    result = bytearray((len(data) * bits + 7) // 8)

    for index, value in enumerate(data):
        _write_bits(result, index * bits, value, bits)

    return result


class ShipType(IntEnum):
    '''AIS ship and cargo type values.'''

    SAILING = 36
    PLEASURE_CRAFT = 37


class RS109Config:
    '''RS-109M configuration EEPROM representation.

    The class keeps the original byte layout:

    Byte 0:
        Transmission interval / 30 seconds

    Bytes 1-4:
        MMSI

    Bytes 5-24:
        Vessel name

    Bytes 25-27:
        Serial number and unit model

    Bytes 28-30:
        Vendor ID

    Byte 31:
        Ship type

    Bytes 32-37:
        Callsign

    Bytes 38-41:
        Reference dimensions
    '''

    CONFIG_LENGTH = 0x40

    OFFSET_INTERVAL = 0
    OFFSET_MMSI = 1
    OFFSET_NAME = 5
    OFFSET_SERIAL = 25
    OFFSET_VENDOR = 28
    OFFSET_SHIP_TYPE = 31
    OFFSET_CALLSIGN = 32
    OFFSET_REFA = 38
    OFFSET_REFB = 39
    OFFSET_REFC = 40
    OFFSET_REFD = 41

    NAME_LENGTH = 20
    CALLSIGN_LENGTH = 6

    DEFAULT_CONFIG = bytes([
        0x04, 0x2d, 0xd2, 0x7f, 0x06,
        0x31, 0x30, 0x39, 0x30, 0x34,
        0x30, 0x31, 0x37, 0x33, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20,
        0x01, 0x00, 0x00, 0xe0, 0x24,
        0x01, 0x00, 0x35, 0x3d, 0xcb,
        0xf1, 0x23, 0x00, 0x08, 0xa0,
        0x00, 0x00,
    ]) + bytes([0xff] * (CONFIG_LENGTH - 42))


    def __init__(self, config: bytes | bytearray | None = None) -> None:
        self.config = config

    @property
    def config(self) -> bytearray:
        return self._config

    @config.setter
    def config(self, value: bytes | bytearray | None) -> None:
        if value is None:
            self._config = bytearray(self.DEFAULT_CONFIG)
            return

        if len(value) > 0xff:
            value = value[:0xff]

        self._config = bytearray(value)

        if len(self._config) < self.CONFIG_LENGTH:
            self._config.extend(self.DEFAULT_CONFIG[len(self._config):])

    def __repr__(self) -> str:
        return f'[ 0x{self._config.hex( ", 0x")} ]'

    @property
    def mmsi(self) -> int:
        '''Maritime Mobile Service Identity.'''
        return int.from_bytes(
            self._config[
                self.OFFSET_MMSI:
                self.OFFSET_MMSI + 4
            ],
            'little',
        )

    @mmsi.setter
    def mmsi(self, value: int) -> None:
        value = int(value)

        if not 0 <= value <= 0xffffffff:
            raise ValueError('MMSI must fit in 32 bits')

        self._config[
            self.OFFSET_MMSI:
            self.OFFSET_MMSI + 4
        ] = value.to_bytes(4, 'little')

    @property
    def name(self) -> str:
        '''Vessel name.'''
        return bytes(
            self._config[
                self.OFFSET_NAME:
                self.OFFSET_NAME + self.NAME_LENGTH
            ]
        ).decode('ascii', 'ignore').rstrip()

    @name.setter
    def name(self, value: str) -> None:
        encoded = (
            value
            .encode('ascii', 'ignore')
            .upper()
            [:self.NAME_LENGTH]
            .ljust(self.NAME_LENGTH, b' ')
        )

        self._config[
            self.OFFSET_NAME:
            self.OFFSET_NAME + self.NAME_LENGTH
        ] = encoded

    @property
    def interval(self) -> int:
        '''Transmission interval in seconds.'''
        return self._config[self.OFFSET_INTERVAL] * 30

    @interval.setter
    def interval(self, seconds: int) -> None:
        seconds = max(30, min(600, int(seconds)))
        self._config[self.OFFSET_INTERVAL] = seconds // 30

    @property
    def shipncargo(self) -> int:
        return self._config[self.OFFSET_SHIP_TYPE]

    @shipncargo.setter
    def shipncargo(self, value: int) -> None:
        value = int(value)

        if not 0 <= value <= 255:
            raise ValueError('ship type must be between 0 and 255')

        self._config[self.OFFSET_SHIP_TYPE] = value

    @property
    def callsign(self) -> str:
        '''Vessel callsign.

        The RS-109 stores callsigns as reversed AIS 6-bit data.
        '''
        raw = decode_ais6(
            self._config[
                self.OFFSET_CALLSIGN:
                self.OFFSET_CALLSIGN + self.CALLSIGN_LENGTH
            ],
            6,
            True,
        )
        return ''.join(
            char
            for char in bytes(raw[::-1]).decode(
                'ascii',
                'ignore',
            )
            if char.isalnum()
        )

    @callsign.setter
    def callsign(self, value: str) -> None:
        clean = ''.join(char for char in value.upper() if char.isalnum())
        encoded = encode_ais6(clean[::-1], 6, True,)
        encoded = encoded[:self.CALLSIGN_LENGTH]

        self._config[
            self.OFFSET_CALLSIGN:
            self.OFFSET_CALLSIGN + self.CALLSIGN_LENGTH
        ] = encoded.ljust(
            self.CALLSIGN_LENGTH,
            b'\x00',
        )

    @property
    def vendorid(self) -> str:
        '''Three-character AIS vendor identifier.'''
        chars = bytearray([
            (self._config[29] >> 4)
            | ((self._config[30] & 0x03) << 4)
            | 0x40,

            (self._config[28] >> 6)
            | ((self._config[29] & 0x07) << 2)
            | 0x40,

            (self._config[28] & 0x3f)
            | 0x40,
        ])
        return ''.join(
            char
            for char in chars.decode(
                'ascii',
                'ignore',
            )
            if char.isalnum()
        )

    @vendorid.setter
    def vendorid(self, value: str) -> None:
        clean = (
            ''.join(
                char
                for char in value.upper()
                if char.isalnum()
            )
            .ljust(3, '\x00')
            [:3]
        )

        data = clean.encode('ascii')

        self._config[28] = ((data[2] & 0x3f) | ((data[1] << 6) & 0xff))
        self._config[29] = (((data[1] >> 2) & 0x0f) | ((data[0] << 4) & 0xff))
        self._config[30] = ((self._config[30] & 0xf0) | ((data[0] >> 4) & 0x0f))

    @property
    def unitmodel(self) -> int:
        '''AIS unit model code.'''
        return self._config[27] >> 4

    @unitmodel.setter
    def unitmodel(self, value: int) -> None:
        value = int(value)
        if not 0 <= value <= 15:
            raise ValueError('unit model must be between 0 and 15')

        self._config[27] = ((self._config[27] & 0x0f) | (value << 4))

    @property
    def sernum(self) -> int:
        '''Unit serial number.'''
        return (
            self._config[25]
            | (self._config[26] << 8)
            | ((self._config[27] & 0x0f) << 16)
        )

    @sernum.setter
    def sernum(self, value: int) -> None:
        value = int(value)
        if not 0 <= value <= 0xfffff:
            raise ValueError('serial number must fit in 20 bits')

        self._config[25] = value & 0xff
        self._config[26] = (value >> 8) & 0xff
        self._config[27] = (self._config[27] & 0xf0) | ((value >> 16) & 0x0f)

    @property
    def refa(self) -> int:
        '''Reference point A distance.'''
        return _read_bits(self._config, 38 * 8 + 4, 9)

    @refa.setter
    def refa(self, value: int) -> None:
        self._set_reference(38 * 8 + 4, value, 'reference A')

    @property
    def refb(self) -> int:
        return _read_bits(self._config, 39 * 8 + 3, 9)

    @refb.setter
    def refb(self, value: int) -> None:
        self._set_reference(39 * 8 + 3, value, 'reference B')

    @property
    def refc(self) -> int:
        return _read_bits(self._config, 40 * 8 + 2, 6)

    @refc.setter
    def refc(self, value: int) -> None:
        value = int(value)
        if not 0 <= value <= 63:
            raise ValueError('reference C must be between 0 and 63')

        _write_bits(self._config, 40 * 8 + 2, value, 6)

    @property
    def refd(self) -> int:
        return _read_bits(self._config, 41 * 8, 6)

    @refd.setter
    def refd(self, value: int) -> None:
        value = int(value)
        if not 0 <= value <= 63:
            raise ValueError('reference D must be between 0 and 63')

        _write_bits(self._config, 41 * 8, value, 6)

    def _set_reference(self, bit_offset: int, value: int, name: str,) -> None:
        value = int(value)
        if not 0 <= value <= 511:
            raise ValueError(f'{name} must be between 0 and 511')

        _write_bits(self._config, bit_offset, value, 9)

import serial


class RS109SerialError(Exception):
    '''Raised when communication with the RS-109 fails.'''


class SerialProtocol:
    '''RS-109 serial communication handler.'''

    BAUDRATE = 115200
    PASSWORD_LENGTH = 6

    def __init__(self, device: str) -> None:
        self.serial = serial.Serial(
            port=device,
            baudrate=self.BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=3,
            write_timeout=3,
        )
        self._wake_device()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.serial.close()

    def _wake_device(self) -> None:
        self.serial.rts = False
        self.serial.rts = True
        self.serial.read(0xffff)

    def _command(
        self,
        data: bytes,
        expected: bytes,
        extra: int = 0,
        retries: int = 3,
    ) -> bytes:
        for _ in range(retries):
            self.serial.reset_input_buffer()
            self.serial.write(data)
            response = self.serial.read(len(expected))
            if response == expected:
                if extra:
                    response += self.serial.read(extra)

                return response

        raise RS109SerialError(f'Unexpected response: {response.hex()}')

    def authenticate(self, password: str | None = None) -> None:
        if password is None:
            command = bytes([0x59, 0x01, 0x42, 0x00])
        else:
            if not password.isdigit():
                raise ValueError('password must contain only digits')

            prepared = (password.encode() + b'000000')[:self.PASSWORD_LENGTH]
            command = bytes([0x59, 0x01, 0x42, self.PASSWORD_LENGTH]) + prepared

        try:
            self._command(command, b'\x95\x20')
        except RS109SerialError:
            # Some devices accept empty authentication
            self._command(bytes([0x59, 0x01, 0x42, 0x00]), b'\x95\x20')

    def read_config(self, length: int = RS109Config.CONFIG_LENGTH) -> RS109Config:
        response = self._command(
            bytes([0x51, length]),
            bytes([0x25, length]),
            extra=length,
        )
        return RS109Config(response[2:])

    def write_config(
        self,
        config: RS109Config,
        length: int = RS109Config.CONFIG_LENGTH,
    ) -> None:
        self._command(
            bytes([0x55, length]) + config.config[:length],
            bytes([0x75, length]),
        )

def apply_arguments(config: RS109Config, args) -> None:
    fields = (
        'mmsi',
        'name',
        'interval',
        'shipncargo',
        'callsign',
        'vendorid',
        'unitmodel',
        'sernum',
        'refa',
        'refb',
        'refc',
        'refd',
    )
    for field in fields:
        value = getattr(args, field)
        if value is not None:
            setattr(config, field, value)

config = RS109Config()

if args.device:
    with SerialProtocol(args.device) as device:
        device.authenticate(args.password)
        if not args.noread:
            config = device.read_config()

apply_arguments(config, args)

print(config)

if args.write:
    with SerialProtocol(args.device) as device:
        device.authenticate(args.password)
        device.write_config(config)


import argparse


def create_argument_parser() -> argparse.ArgumentParser:
    '''Create command-line argument parser.'''
    parser = argparse.ArgumentParser(
        description='RS-109M Net Locator AIS buoy configurator'
    )
    parser.add_argument(
        '-d',
        '--device',
        help='serial port device (for example /dev/ttyUSB0)',
    )
    parser.add_argument('-m', '--mmsi', type=int, help='MMSI')
    parser.add_argument('-n', '--name', help='ship name')
    parser.add_argument(
        '-i',
        '--interval',
        type=int,
        help='transmit interval in seconds [30..600]',
    )
    parser.add_argument(
        '-t',
        '--type',
        dest='shipncargo',
        type=int,
        help='ship type',
    )
    parser.add_argument('-c', '--callsign', help='call sign')
    parser.add_argument('-v', '--vendorid', help='AIS unit vendor ID')
    parser.add_argument(
        '-u',
        '--unitmodel',
        type=int,
        help='AIS unit model code',
    )
    parser.add_argument(
        '-s',
        '--sernum',
        type=int,
        help='AIS unit serial number',
    )
    parser.add_argument('-A', '--refa', type=int, help='reference A')
    parser.add_argument('-B', '--refb', type=int, help='reference B')
    parser.add_argument('-C', '--refc', type=int, help='reference C')
    parser.add_argument('-D', '--refd', type=int, help='reference D')
    parser.add_argument('-P', '--password', help='device password')
    parser.add_argument('--setpass', help='set new password')
    parser.add_argument('--clearpass', action='store_true', help='clear password')
    parser.add_argument(
        '-E',
        '--extended',
        action='store_true',
        help='use extended configuration size',
    )
    parser.add_argument(
        '-W',
        '--write',
        action='store_true',
        help='write configuration',
    )
    parser.add_argument(
        '-R',
        '--noread',
        action='store_true',
        help='do not read configuration',
    )
    return parser


def print_config(config: RS109Config, length: int) -> None:
    '''Display configuration values.'''
    print()
    print(f'  MMSI: {config.mmsi}')
    print(f'  Name: {config.name}')
    print(f'  TX interval (s): {config.interval}')
    print(f'  Ship type: {config.shipncargo}')
    print(f'  Callsign: {config.callsign}')
    print(f'  VendorID: {config.vendorid}')
    print(f'  UnitModel: {config.unitmodel}')
    print(f'  UnitSerial: {config.sernum}')
    print(
        f'  Reference point A (m): '
        f'{config.refa} '
        f'(may be battery voltage '
        f'{config.refa / 10:.1f}V)'
    )
    print(f'  Reference point B (m): {config.refb}')
    print(f'  Reference point C (m): {config.refc}')
    print(f'  Reference point D (m): {config.refd}')
    print()

    print(
        '[ 0x'
        + config.config[:length].hex(', 0x')
        + ' ]'
    )


def update_config_from_args(
    config: RS109Config,
    args: argparse.Namespace,
) -> None:
    '''
    Apply command line overrides.
    '''

    properties = (
        'mmsi',
        'name',
        'interval',
        'shipncargo',
        'callsign',
        'vendorid',
        'unitmodel',
        'sernum',
        'refa',
        'refb',
        'refc',
        'refd',
    )

    for name in properties:

        value = getattr(
            args,
            name,
        )

        if value is not None:

            setattr(
                config,
                name,
                value,
            )


def main() -> int:

    parser = create_argument_parser()

    args = parser.parse_args()

    config_length = (
        0xff
        if args.extended
        else RS109Config.CONFIG_LENGTH
    )

    config = RS109Config()

    if args.device:

        with SerialProtocol(
            args.device
        ) as device:

            device.authenticate(
                args.password
            )

            if args.clearpass:
                raise NotImplementedError(
                    'password clearing not implemented '
                    'in refactored version yet'
                )

            if args.setpass:
                raise NotImplementedError(
                    'password changing not implemented '
                    'in refactored version yet'
                )

            if not args.noread:

                config = device.read_config(
                    config_length
                )


    update_config_from_args(
        config,
        args,
    )


    print_config(
        config,
        config_length,
    )


    if args.write:

        if not args.device:

            raise SystemExit(
                'Must supply serial device '
                'with -d option'
            )

        with SerialProtocol(
            args.device
        ) as device:

            device.authenticate(
                args.password
            )

            device.write_config(
                config,
                config_length,
            )

        print(
            'Config written successfully!'
        )


    return 0


if __name__ == '__main__':

    raise SystemExit(
        main()
    )
