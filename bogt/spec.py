
import json
import os


_tables = None


def table(table):
    global _tables
    if _tables is None:
        _load_tables()
    return _tables[table]


def patch():
    return table('PATCH')


def system():
    return table('SYSTEM')


def midi():
    return table('MIDI')


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
