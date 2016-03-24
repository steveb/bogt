
import json
import os


_tables = None


def table(table_name):
    global _tables
    if _tables is None:
        _load_tables()
    try:
        return _tables[table_name]
    except KeyError:
        raise ValueError('Unknown table: %s' % (table_name))


def patch():
    return table('PATCH')


def system():
    return table('SYSTEM')


def midi():
    return table('MIDI')


def table_name(self, block):
    if block == 0x0:
        return 'SYSTEM'
    if block == 0x2:
        return 'MIDI'
    if block >= 0x1000:
        return 'PATCH'
    raise ValueError('Unknown address block: %02x', block)


def table_entry(self, table_name, table_key):
    t = table(table_name)
    try:
        return t[table_key]
    except KeyError:
        raise ValueError('Unknown key in  %s: %s' % (table_name, table_key))


def _load_tables():
    global _tables
    spec_dir = os.path.dirname(__file__)
    spec_path = os.path.join(spec_dir, 'spec.json')
    with open(spec_path) as fp:
        tables = json.load(fp)
    for t in tables.values():
        for k, v in t.items():
            # convert keys to int
            del t[k]
            t[int(k, 0)] = v
    _tables = tables
