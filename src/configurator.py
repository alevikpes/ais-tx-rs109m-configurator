

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
    _config = None

    def __init__(self, config=None):
        self.config = config

    def __repr__(self):
        return f'[ 0x {self._config.hex('#').replace("#", ", 0x")} ]'

    @staticmethod
    def _fromxbit(ba, x=6):
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

            if (b[i] & 0x20) != 0x20 and b[i] != 0:
                # not a digit, is alpha
                b[i] = (b[i] & 0x1f) | 0x40

        return b

    @staticmethod
    def _toxbit(ba: bytes, x: int=6):
        if ((x < 1) or (x > 7)):
            raise ValueError('BitLen must between 1 and 7')

        if len(ba) < 1:
            return [0xff, 0xff, 0xff, 0xff, 0xff, 0xff]

        ba = bytearray(ba.decode().upper().encode('ascii'))

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

    def _get_ascii(self, offset, length, encoding='ascii', strip=True):
        s = bytes(self._config[offset:offset + length]).decode(encoding)
        return s.rstrip(' \x00') if strip else s

    def _set_ascii(
        self,
        offset,
        length,
        value,
        encoding='ascii',
        pad=' ',
        uppercase=False
    ):
        value = str(value)
        if uppercase:
            value = value.upper()

        data = (
            value.encode(encoding, 'ignore')[:length]
            .ljust(length, pad.encode(encoding))
        )
        self._config[offset:offset + length] = data

    def _get_xbit(self, offset, length, width=6, reverse=False):
        s = self._fromxbit(
            self._config[offset:offset + length],
            width,
            True
        ).decode('ascii')

        if reverse:
            s = s[::-1]

        return s.rstrip(' @\x00')


    def _set_xbit(self, offset, length, value, width=6, reverse=False):
        value = ''.join(
            c.upper()
            for c in str(value)
            if c.isalnum()
        )

        if reverse:
            value = value[::-1]

        encoded = self._toxbit(value, width, True)
        self._config[offset:offset + length] = encoded[:length].ljust(length, b'\x00')

    ### Config ###
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
                config[:clen] + self.default_config[clen:]
            )

    ### MMSI ###
    @property
    def mmsi(self):
        return self._get_uint(1, 4)

    @mmsi.setter
    def mmsi(self, mmsi):
        self._set_uint(1, 4, mmsi)

    ### Ship Name ###
    @property
    def ship_name(self):
        return self._get_ascii(5, 20)

    @ship_name.setter
    def ship_name(self, name):
        self._set_ascii(
            5,
            20,
            name,
            uppercase=True,
            pad=' '
        )

    ### Interval ###
    @property
    def interval(self):
        return self._get_byte(0) * 30

    @interval.setter
    def interval(self, seconds):
        seconds = max(30, min(600, int(seconds)))
        self._set_byte(0, seconds // 30)

    ### Ship Type ###
    @property
    def ship_type(self):
        return self._get_byte(31)

    @ship_type.setter
    def ship_type(self, shiptype):
        self._set_byte(31, shiptype)

    ### Vendor ID ###
    @property
    def vendor_id(self):
        chars = []
        for start_bit in (29 * 8 + 4, 28 * 8 + 6, 28 * 8):
            c = chr(self._get_bits(start_bit, 6) | 0x40)
            if c.isalnum():
                chars.append(c)

        return ''.join(chars)

    @vendor_id.setter
    def vendor_id(self, vid):
        safe_vid = (
            vid.encode('ascii', 'ignore')
               .decode()
               .upper()
               .ljust(3, '\x00')[:3]
        )
        self._set_bits(29 * 8 + 4, 6, ord(safe_vid[0]) & 0x3f)
        self._set_bits(28 * 8 + 6, 6, ord(safe_vid[1]) & 0x3f)
        self._set_bits(28 * 8,     6, ord(safe_vid[2]) & 0x3f)

    ### Unit Model ###
    @property
    def unit_model(self):
        return self._get_bits(27 * 8 + 4, 4)

    @unit_model.setter
    def unit_model(self, unitmodel):
        self._set_bits(27 * 8 + 4, 4, value)

    ### Serial Number ###
    @property
    def ser_num(self):
        return self._get_bits(25 * 8, 20)

    @ser_num.setter
    def ser_num(self, sernum):
        self._set_bits(25 * 8, 20, value)

    ### Call Sign ###
    @property
    def call_sign(self):
        return self._get_xbit(32, 6, reverse=True)

    @call_sign.setter
    def call_sign(self, value):
        self._set_xbit(32, 6, value, reverse=True)

    @property
    def ais2bow(self):
        return self._get_bits(38 * 8 + 3, 9)

    @ais2bow.setter
    def ais2bow(self, value):
        self._set_bits(38 * 8 + 3, 9, value)

    @property
    def ais2stern(self):
        return self._get_bits(39 * 8, 9)

    @ais2stern.setter
    def ais2stern(self, value):
        self._set_bits(39 * 8, 9, value)

    @property
    def ais2port(self):
        return self._get_bits(40 * 8 + 2, 6)

    @ais2port.setter
    def ais2port(self, c):
        self._set_bits(40 * 8 + 2, 6, value)

    @property
    def ais2star(self):
        return self._get_bits(41 * 8, 6)

    @ais2star.setter
    def ais2star(self, d):
        self._set_bits(41 * 8, 6, value)
