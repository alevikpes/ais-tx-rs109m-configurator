

class Configurator:

    default_config = bytearray([
        0x04, 0x2d, 0xd2, 0x7f, 0x06, 0x31, 0x30, 0x39,
        0x30, 0x34, 0x30, 0x31, 0x37, 0x33, 0x20, 0x20,
        0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
        0x20, 0x01, 0x00, 0x00, 0xe0, 0x24, 0x01, 0x00,
        0x35, 0x3d, 0xcb, 0xf1, 0x23, 0x00, 0x08, 0xa0,
        0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,

        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff
    ])
    default_len = 0x40

    def __init__(self, config=None):
        self.set_config(config)

    def __repr__(self):
        return f'[ 0x {self._config.hex('#').replace("#", ", 0x")} ]'

    def _get_uint(self, offset, length):
        return int.from_bytes(self._config[offset:offset + length], 'little')

    def _set_uint(self, offset, length, value):
        self._config[offset:offset + length] \
            = int(value).to_bytes(length, 'little')

    def _get_bits(self, start_bit, length):
        """Read a bitfield.

        start_bit: bit offset from the beginning of the config.
                   Bit 0 is the least-significant bit of byte 0.
        length:    number of bits.
        """
        value = int.from_bytes(self._config, 'little')
        mask = (1 << length) - 1
        return (value >> start_bit) & mask

    def _set_bits(self, start_bit, length, field_value):
        """Write a bitfield.

        start_bit: bit offset from the beginning of the config.
        length:    number of bits.
        """
        field_value = int(field_value)
        if not 0 <= field_value < (1 << length):
            raise ValueError(
                f'value must fit in {length} bits '
                f'(0..{(1 << length) - 1})'
            )

        value = int.from_bytes(self._config, 'little')

        mask = ((1 << length) - 1) << start_bit
        value &= ~mask
        value |= field_value << start_bit

        self._config[:] = value.to_bytes(len(self._config), 'little')

    def _get_byte(self, offset):
        return self._config[offset]

    def _set_byte(self, offset, value):
        self._config[offset] = int(value) & 0xff

    def _get_ascii(self, offset, length):
        return bytes(self._config[offset:offset+length]).decode('ascii')

    def _set_ascii(self, offset, length, value):
        self._config[offset:offset+length] = (
            value.encode('ascii', 'ignore')[:length]
            .ljust(length, b' ')
        )

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        # TODO: implement differently, as setting config as slices
        # config[34:38] might be convenient
        if config is None:
            # self._config = self.default_config[:self.default_len]
            self._config = self.default_config.copy()
        else:
            clen = min(len(config), 0xff)
            self._config = bytearray(
                config[:clen] +
                self.default_config[clen:]
            )

    @property
    def mmsi(self):
        return self._get_uint(1, 4)

    @mmsi.setter
    def mmsi(self, mmsi):
        self._set_uint(1, 4, mmsi)

    @property
    def ship_name(self):
        name = bytes(self._config[5:25]).decode('ascii').strip()
        return name

    @ship_name.setter
    def ship_name(self, name):
        # TODO: check for invalid chars, this one is incomplete
        safe_name = name \
            .encode('ascii', 'ignore') \
            .decode() \
            .upper() \
            .ljust(20, ' ') \
            .encode('ascii')
        self._config[5:25] = safe_name

    @property
    def interval(self):
        return self._get_byte(0) * 30

    @interval.setter
    def interval(self, seconds):
        seconds = max(30, min(600, int(seconds)))
        self._set_byte(0, seconds // 30)

    @property
    def ship_type(self):
        return self._get_byte(31)

    @ship_type.setter
    def ship_type(self, shiptype):
        self._set_byte(31, shiptype)

    @property
    def vendor_id(self):
        vid = [
            (self._config[29] >> 4) | ((self._config[30]  & 0x03) << 4) | 0x40,
            (self._config[28] >> 6) | ((self.config[29] & 0x07) << 2) | 0x40,
            (self._config[28] & 0x3f) | 0x40,
        ]
        return  ''.join(c if c.isalnum() else '' for c in bytes(vid).decode())

    @vendor_id.setter
    def vendor_id(self, vid):
        # TODO: check for invalid chars, this one is incomplete
        safe_vid = vid \
            .encode('ascii', 'ignore') \
            .decode() \
            .upper() \
            .ljust(3, '\x00')[:3] \
            .encode('ascii')
        print(safe_vid)
        self._config[28] = (safe_vid[2] & 0x3f) | ((safe_vid[1] << 6 ) & 0xff)
        self._config[29] = (
            ((safe_vid[1] >> 2) & 0x0f) |
            ((safe_vid[0] << 4) & 0xff)
        )
        self._config[30] = (
            (self._config[30] & ~0x0f) |
            ((safe_vid[0] & 0x3f) >> 4)
        )

    @property
    def unit_model(self):
        unitmodel = self._config[27] >> 4
        return unitmodel

    @unit_model.setter
    def unit_model(self, unitmodel):
        unitmodel = int(unitmodel)
        if unitmodel < 0 or unitmodel > 15:
            raise ValueError('UnitModel must be 0 < unitmodel <= 15')

        self._config[27] = (
            (self._config[27] & 0x0f) |
            ((int(unitmodel) & 0x0f) << 4)
        )

    @property
    def ser_num(self):
        low16 = self._get_uint(25, 2)
        high4 = self._config[27] & 0x0f
        return low16 | (high4 << 16)

    @ser_num.setter
    def ser_num(self, sernum):
        sernum = int(sernum)
        if not 0 <= sernum <= 0xfffff:
            raise ValueError(
                'Serial number must be an integer between 0 and 1048575 digits'
            )

        self._set_uint(25, 2, sernum & 0&ffff)
        self._config[27] = (self._config[27] & 0xf0) | ((sernum >> 16) & 0x0f)

    @property
    def call_sign(self):
        # TODO: check if it is 32:37 or 32:38
        # derek@conniffe.com - changed to 32:38 to
        # support valid 7 digit callsigns
        s = fromxbit(self._config[32:38], 6, True).decode('ascii')[::-1]
        return ''.join(c if c.isalnum() else '' for c in s)

    @call_sign.setter
    def call_sign(self, cs):
        safe_cs = ''.join(c if c.isalnum() else '' for c in cs)
        # derek@conniffe.com - changed to 32:38 to
        # support valid 7 digit callsigns
        self._config[32:38] = toxbit(safe_cs[::-1])

    @property
    def ais2bow(self):
        return (self._config[39] >> 5) | ((self.config[38] & ((1<<6) -1)) << 3)

    @ais2bow.setter
    def ais2bow(self, a):
        if int(a) > (1<<9):
            raise ValueError('Reference a must be <= 511')

        if int(a) < 0:
            raise ValueError('Reference a must be >= 0')

        self._config[39] = (
            (self._config[39] & ((1<<5) -1)) |
            (((int(a) & ((1<<6) -1)) << 5) & 0xff)
        )
        self._config[38] = (
            (self._config[38] & ~((1<<4) -1)) |
            ((int(a) & ((1<<9) -1)) >> 3)
        )

    @property
    def ais2stern(self):
        return (
            (self._config[40] >> 4) |
            ((self._config[39] & ((1<<5) -1)) << 4)
        )

    @ais2stern.setter
    def ais2stern(self, b):
        if int(b) > (1<<9):
            raise ValueError('Reference b must be <= 511')

        if int(b) < 0:
            raise ValueError('Reference b must be >= 0')

        self._config[40] = (
            (self._config[40] & ((1<<4) -1)) |
            (((int(b) & ((1<<6) -1)) << 4) & 0xff)
        )
        self._config[39] = (
            (self._config[39] & ~((1<<5) -1)) |
            ((int(b) & ((1<<9) -1)) >> 4)
        )

    @property
    def ais2port(self):
        return (self._config[41] >> 6) | ((self._config[40] & ((1<<4) -1)) << 2)

    @ais2port.setter
    def ais2port(self, c):
        if int(c) > (1<<6):
            raise ValueError('Reference c must be <= 63')

        if int(c) < 0:
            raise ValueError('Reference c must be >= 0')

        self._config[41] = (
            (self._config[41] & ((1<<6) -1)) |
            (((int(c) & ((1<<6) -1)) << 6) & 0xff)
        )
        self._config[40] = (
            (self._config[40] & ~((1<<4) -1)) |
            ((int(c) & ((1<<6) -1)) >> 2)
        )

    @property
    def ais2star(self):
        return self._config[41] & ((1<<6) -1)

    @ais2star.setter
    def ais2star(self, d):
        if int(d) > (1<<6):
            raise ValueError('Reference d must be <= 63')

        if int(d) < 0:
            raise ValueError('Reference d must be >= 0')

        self._config[41] = (
            (self._config[41] & ~((1<<6) -1)) |
            (int(d) & ((1<<6) -1))
        )
