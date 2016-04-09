
import collections
import json
import os


_tables = None
_max_table_keys = collections.defaultdict(int)


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


def table_name(block):
    if block == 0x0:
        return 'SYSTEM'
    if block == 0x2:
        return 'MIDI'
    if block >= 0x1000:
        return 'PATCH'
    raise ValueError('Unknown address block: %02x', block)


def table_entry(table_name, table_key):
    t = table(table_name)
    try:
        return t[table_key]
    except KeyError:
        raise ValueError('Unknown key in %s: %s' % (
            table_name, hex(table_key)))


def next_table_key(table_name, table_key):
    t = table(table_name)
    max_key = _max_table_keys[table_name]
    if table_key > max_key:
        raise KeyError()
    while table_key not in t and table_key <= max_key:
        table_key += 1
    return table_key


def _reverse_table(tables, table_name):
    table = tables.get(table_name)
    reverse_table = dict([(v, k) for k, v in table.items()])
    tables['%s REVERSE' % table_name] = reverse_table


def _load_tables():
    global _tables
    spec_dir = os.path.dirname(__file__)
    spec_path = os.path.join(spec_dir, 'spec.json')
    with open(spec_path) as fp:
        tables = json.load(fp)
    for table_name, t in tables.items():
        for k, v in t.items():
            # convert keys to int
            del t[k]
            int_key = int(k, 0)
            t[int_key] = v
            if _max_table_keys[table_name] < int_key:
                _max_table_keys[table_name] = int_key
    _reverse_table(tables, 'USER PATCH BLOCK')
    _reverse_table(tables, 'BYTENUM TO INDEX')
    _tables = tables
