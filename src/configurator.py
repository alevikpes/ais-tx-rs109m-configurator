

class Configurator:

    extended_config = bytearray([
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
    ])  # Length of this is `0xf0` (240 bytes)
    default_len = 0x40  # 64 bytes
    _config = None

    def __init__(self, config=None):
        self.config = config

    def __repr__(self):
        return f'[ 0x {self._config.hex('#').replace("#", ", 0x")} ]'

    @staticmethod
    def fromxbit(ba, x = 6, digitalphaencoding = True):
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

    @staticmethod
    def toxbit(ba, x = 6, digitalphaencoding = True):
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

    ### Config ###
    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        # TODO: implement differently, as setting config as slices
        # config[34:38] might be convenient
        if config == []:
            self._config = self.extended_config[:self.default_len]
        else:
            clen = 0xff if (len(config) > 0xff) else len(config)
            self._config = bytearray(
                config[0:clen] + self.extended_config[clen:]
            )

    ### MMSI ###
    @property
    def mmsi(self):
        mmsi = self._config[1] \
            + (self._config[2] << 8) \
            + (self._config[3] << 16) \
            + ((self._config[4] & 0xff) << 24)
        return mmsi

    @mmsi.setter
    def mmsi(self, mmsi):
        mmsi = int(mmsi)
        self._config[1] = mmsi & 0xff
        self._config[2] = (mmsi >> 8) & 0xff
        self._config[3] = (mmsi >> 16) & 0xff
        self._config[4] = (mmsi >> 24) & 0xff

    ### Ship name ###
    @property
    def name(self):
        name = bytes(self._config[5:25]).decode('ascii').strip()
        return name

    @name.setter
    def name(self, name):
        # TODO: check for invalid chars, this one is incomplete
        safe_name = name \
            .encode('ascii', 'ignore') \
            .decode() \
            .upper() \
            .ljust(20, ' ') \
            .encode('ascii')
        self._config[5:25] = safe_name

    ### Interval ###
    @property
    def interval(self):
        return self._config[0] * 30

    @interval.setter
    def interval(self, seconds):
        seconds = int(seconds)
        if seconds > 600:
            seconds = 600  # maximum 10 minutes

        if seconds < 30:
            seconds = 30  # minimum 30 seconds

        self._config[0] = seconds // 30

    ### Ship type ###
    @property
    def shipncargo(self):
        return int(self._config[31])

    @shipncargo.setter
    def shipncargo(self,shiptype):
        self._config[31] = int(shiptype) & 0xff

    ### Vendor ID ###
    @property
    def vendorid(self):
        vid = [
            (self._config[29] >> 4) | ((self._config[30]  & 0x03) << 4) | 0x40,
            (self._config[28] >> 6) | ((self.config[29] & 0x07) << 2) | 0x40,
            (self._config[28] & 0x3f) | 0x40,
        ]
        return  ''.join(c if c.isalnum() else '' for c in bytes(vid).decode())

    @vendorid.setter
    def vendorid(self, vid):
        # TODO: check for invalid chars, this one is incomplete
        safe_vid = vid \
            .encode('ascii', 'ignore') \
            .decode() \
            .upper() \
            .ljust(3, '\x00')[:3] \
            .encode('ascii')
        #print(safe_vid)
        self._config[28] = (safe_vid[2] & 0x3f) | ((safe_vid[1] << 6 ) & 0xff)
        self._config[29] = ((safe_vid[1] >> 2) & 0x0f) | ((safe_vid[0] << 4) & 0xff)
        self._config[30] = (self._config[30] & ~0x0f) | ((safe_vid[0] & 0x3f) >> 4)

    ### Unit model ###
    @property
    def unitmodel(self):
        unitmodel = self._config[27] >> 4
        return unitmodel

    @unitmodel.setter
    def unitmodel(self, unitmodel):
        unitmodel = int(unitmodel)
        if unitmodel < 0 or unitmodel > 15:
            raise ValueError("UnitModel must be 0 < unitmodel <= 15")

        self._config[27] = (
            (self._config[27] & 0xf0) | ((int(unitmodel) & 0x0f) << 4)
        )

    ### Serial number ###
    @property
    def sernum(self):
        sernum = (
            self._config[25] +
            (self._config[26] << 8) +
            ((self._config[27] & 0x0f) << 16)
        )
        return sernum

    @sernum.setter
    def sernum(self, sernum):
        sernum = int(sernum)
        if sernum < 0 or sernum > ((1 << 20) -1):
            raise ValueError('UnitSernum must be 0 <= sernum <=', ((1<<20)-1))

        self._config[25] = sernum & 0xff
        self._config[26] = (sernum >> 8) & 0xff
        self._config[27] = (self._config[27] & 0xf0) | ((sernum >> 16) & 0x0f)

    ### Call sign ###
    @property
    def callsign(self):
        # TODO: check if it is 32:37 or 32:38
        # derek@conniffe.com - changed to 32:38 to
        # support valid 7 digit callsigns
        s = fromxbit(self._config[32:38], 6, True).decode('ascii')[::-1]
        return ''.join(c if c.isalnum() else '' for c in s)

    @callsign.setter
    def callsign(self, cs):
        safe_cs = ''.join(c if c.isalnum() else '' for c in cs)
        # derek@conniffe.com - changed to 32:38 to
        # support valid 7 digit callsigns
        self._config[32:38] = toxbit(safe_cs[::-1])

    @staticmethod
    def _validate(value, bits, name):
        value = int(value)
        max_value = (1 << bits) - 1

        if not 0 <= value <= max_value:
            raise ValueError(f'{name} must be between 0 and {max_value}')

        return value

    ### AIS to bow ###
    @property
    def refa(self):
        return (self._config[39] >> 5) | ((self.config[38] & ((1 << 6) - 1)) << 3)

    @refa.setter
    def refa(self, a):
        a = self._validate(a, 9, 'Reference a')

        self._config[39] = (
            (self._config[39] & ((1 << 5) - 1)) |
            (((a & ((1 << 6) - 1)) << 5) & 0xff)
        )
        self._config[38] = (
            (self._config[38] & ~((1 << 4) - 1)) |
            ((a & ((1 << 9) - 1)) >> 3)
        )

    ### AIS to stern ###
    @property
    def refb(self):
        return (self._config[40] >> 4) | ((self._config[39] & ((1 << 5) - 1)) << 4)

    @refb.setter
    def refb(self, b):
        b = self._validate(b, 9, 'Reference b')

        self._config[40] = (
            (self._config[40] & ((1 << 4) - 1)) |
            (((b & ((1 << 6) - 1)) << 4) & 0xff)
        )
        self._config[39] = (
            (self._config[39] & ~((1 << 5) - 1)) |
            ((b & ((1 << 9) - 1)) >> 4)
        )

    ### AIS to port ###
    @property
    def refc(self):
        return (self._config[41] >> 6) | ((self._config[40] & ((1 << 4) - 1)) << 2)

    @refc.setter
    def refc(self, c):
        c = self._validate(c, 6, 'Reference c')

        self._config[41] = (
            (self._config[41] & ((1 << 6) - 1)) |
            (((c & ((1 << 6) - 1)) << 6) & 0xff)
        )
        self._config[40] = (
            (self._config[40] & ~((1 << 4) - 1)) |
            ((c & ((1 << 6) - 1)) >> 2)
        )

    ### AIS to starboard ###
    @property
    def refd(self):
        return self._config[41] & ((1 << 6) - 1)

    @refd.setter
    def refd(self, d):
        d = self._validate(d, 6, 'Reference d')

        self._config[41] = (
            (self._config[41] & ~((1 << 6) - 1)) |
            (d & ((1 << 6) - 1))
        )

    def get_ais_position(self, field_name):
