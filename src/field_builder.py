from src.field_registry import FIELD_TYPES


def build_fields(memory_map):
    fields = {}

    for name, offset, length, ftype in memory_map:
        cls = FIELD_TYPES[ftype]

        # special constructor handling
        if ftype == 'packed_bits':
            fields[name] = cls(offset, 4, 4)
        else:
            fields[name] = cls(offset, length)

    return fields
