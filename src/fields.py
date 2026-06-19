"""Collection of fields classes."""


#class FieldRegistry:
#
#    def __init__(self, memory_map, field_factory):
#        self.fields = {}
#        self.occupied = set()
#
#        for name, offset, length in memory_map:
#            field = field_factory(name, offset, length)
#
#            for i in range(offset, offset + length):
#                if i in self.occupied:
#                    raise ValueError(
#                        f'OVERLAP detected: field {name} at byte {i}'
#                    )
#                self.occupied.add(i)
#
#            self.fields[name] = field
#
#    def get(self, name):
#        return self.fields[name]


class Field:
    """Abstract class for fields."""

    _is_saved = False

    def __init__(self, offset, length):
        self.offset = offset
        self.length = length

    def read(self, config):
        raise NotImplementedError

    def write(self, config, value):
        raise NotImplementedError

    def validate(self, value):
        return True


class UIntField(Field):
    """Unsigned little-endian integer."""

    def validate(self, value):
        try:
            v = int(value)
        except Exception:
            raise ValueError('UIntField requires an integer value')

        max_val = (1 << (self.length * 8)) - 1

        if not (0 <= v <= max_val):
            raise ValueError(
                f'UIntField out of range: 0–{max_val}, got {v}'
            )

        return True

    def read(self, config):
        return int.from_bytes(
            config[self.offset:self.offset+self.length],
            byteorder='little'
        )

    def write(self, config, value):
        if self.validate(value):
            config[self.offset:self.offset+self.length] = (
                int(value).to_bytes(self.length, 'little')
            )
            self._is_saved = True

        return self.is_saved, config


class AsciiField(Field):
    """Fixed length ASCII string."""

    def validate(self, value):
        if not isinstance(value, str):
            raise ValueError('AsciiField requires a string')

        try:
            encoded = value.encode('ascii', errors='strict')
        except Exception:
            raise ValueError('AsciiField contains non-ASCII characters')

        if len(encoded) > self.length:
            raise ValueError(
                f'AsciiField too long: max {self.length}, got {len(encoded)}'
            )

        return True

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

    def validate(self, value):
        if not isinstance(value, str):
            raise ValueError('Ais6BitField requires a string')

        v = value.upper()

        try:
            v.encode('ascii')
        except Exception:
            raise ValueError('Ais6BitField must be ASCII')

        # AIS 6-bit alphabet constraint (approximation)
        # letters, digits, space, and limited punctuation
        allowed = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ')

        for c in v:
            if c not in allowed:
                raise ValueError(
                    f'Ais6BitField invalid character: `{c}`'
                )

        # length check based on encoding capacity
        max_chars = (self.length * 8) // 6

        if len(v) > max_chars:
            raise ValueError(
                f'Ais6BitField too long: max {max_chars}, got {len(v)}'
            )

        return True

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


#class VendorIdField(Field):
#    """AIS 3 character vendor ID."""
#
#    def validate(self, value):
#        if not isinstance(value, str):
#            raise ValueError('VendorIdField requires string')
#
#        v = value.upper()
#
#        if len(v) != 3:
#            raise ValueError('VendorId must be exactly 3 characters')
#
#        try:
#            v.encode('ascii')
#        except Exception:
#            raise ValueError('VendorId must be ASCII')
#
#        # AIS encoding constraint (0x40-based printable range)
#        for c in v:
#            if not ('A' <= c <= 'Z' or '0' <= c <= '9'):
#                raise ValueError(f'Invalid VendorId char: {c}')
#
#        return True
#
#    def read(self, config):
#        b0 = config[28]
#        b1 = config[29]
#        b2 = config[30]
#        chars = [
#            (b0 >> 4) | ((b1 & 0x03) << 4),
#            (b1 >> 2) | ((b2 & 0x0f) << 6),
#            b2 & 0x3f,
#        ]
#        return ''.join(chr(c + 0x40) for c in chars)
#
#    def write(self, config, value):
#        value = value.upper().ljust(3)[:3]
#        data = [ord(c) - 0x40 for c in value]
#        config[28] = data[2] | ((data[1] & 0x03) << 6)
#        config[29] = ((data[1] >> 2) & 0x0f) | (data[0] << 4)
#        config[30] = config[30] & 0xf0 | ((data[0] >> 4) & 0x0f)


class VendorIdField(Field):
    """AIS 3 character vendor ID (custom encoding)."""

    def read(self, config) -> str:
        vid = [
            (config[29] >> 4) | ((config[30] & 0x03) << 4) | 0x40,
            (config[28] >> 6) | ((config[29] & 0x07) << 2) | 0x40,
            (config[28] & 0x3F) | 0x40,
        ]
        return ''.join(c for c in bytes(vid).decode(errors='ignore') if c.isalnum())

    def write(self, config, vid: str) -> None:
        safe_vid = (
            vid.encode('ascii', 'ignore')
               .decode()
               .upper()
               .ljust(3, '\x00')[:3]
               .encode('ascii')
        )

        config[28] = (safe_vid[2] & 0x3F) | ((safe_vid[1] << 6) & 0xFF)
        config[29] = ((safe_vid[1] >> 2) & 0x0F) | ((safe_vid[0] << 4) & 0xFF)
        config[30] = (config[30] & ~0x0F) | ((safe_vid[0] & 0x3F) >> 4)

    def validate(self, config, vid: str) -> bool:
        """
        Validation rules:
        - must be ASCII-safe (after sanitization)
        - must be 1–3 chars after cleaning
        - must be alphanumeric (final representation constraint)
        - must round-trip correctly through storage
        """
        if not isinstance(vid, str):
            return False

        cleaned = vid.encode('ascii', 'ignore').decode().upper()
        if not (1 <= len(cleaned.strip()) <= 3):
            return False

        if not cleaned.strip().isalnum():
            return False

        # round-trip validation
        original = self.read(config)
        self.write(config, vid)
        roundtrip = self.read(config)

        # restore original state (important for validation side-effect safety)
        self.write(config, original)

        return roundtrip == cleaned.strip()


class PackedBitsField(Field):
    """Generic bit-field."""

    def __init__(self, offset, shift, bits):
        super().__init__(offset, 1)
        self.shift = shift
        self.mask = (1 << bits)-1

    def validate(self, value):
        try:
            v = int(value)
        except Exception:
            raise ValueError('PackedBitsField requires integer value')

        if v < 0 or v > self.mask:
            raise ValueError(
                f'PackedBitsField out of range: 0–{self.mask}, got {v}'
            )

        return True

    def read(self, config):
        return (config[self.offset] >> self.shift) & self.mask

    def write(self, config, value):
        config[self.offset] &= ~(self.mask << self.shift)

        config[self.offset] |= (int(value) & self.mask) << self.shift


class AISReferenceField(Field):

    def validate(self, value):
        required = {'bow', 'stern', 'port', 'starboard'}

        if set(value.keys()) != required:
            raise ValueError('AISReferenceField requires bow/stern/port/starboard')

        for k in required:
            v = int(value[k])
            if not (0 <= v <= 0x1FF):
                raise ValueError(f'{k} out of range')

        return True

    def read(self, config):
        b = config

        return {
            'bow': (b[39] >> 5) | ((b[38] & 0x3F) << 3),
            'stern': ((b[39] & 0x1F) << 4) | (b[40] >> 4),
            'port': ((b[40] & 0x0F) << 6) | (b[41] >> 6),
            'starboard': b[41] & 0x3F,
        }

    def write(self, config, value):
        a = int(value['bow'])
        b = int(value['stern'])
        c = int(value['port'])
        d = int(value['starboard'])

        config[38] = (config[38] & 0xC0) | ((a >> 3) & 0x3F)
        config[39] = ((a & 0x07) << 5) | ((b >> 4) & 0x1F)
        config[40] = (config[40] & 0xF0) | (((b & 0x0F) << 4) | ((c >> 6) & 0x0F))
        config[41] = ((c & 0x3F) << 6) | (d & 0x3F)
