
import collections
import json

import mido

from bogt import io  # noqa
from bogt import parsed_sysex
from bogt import spec


EMPTY_LIVESET = {
    "version": "1.0.0",
    "liveSetData": {
        "orderNumber": 1,
        "path": None,
        "image": None,
        "id": "",
        "name": "",
        "url": None
    },
    "patchList": [],
    "device": "GT"
}


def load_tsl_from_file(path, conf):
    with open(path) as f:
        return LiveSet(conf, json.load(f))


def empty_tsl(conf):
    return LiveSet(conf)


def patch_to_midi(conf, session, patch, preset_name):
    values = patch['params']
    if not preset_name:
        preset_name = "TEMPORARY PATCH"

    upb = spec.table('USER PATCH BLOCK REVERSE')
    byte_table = spec.table('BYTENUM TO INDEX REVERSE')
    block = upb[preset_name]
    device_id = conf.get('device_id', 0x00)
    pt = spec.patch()
    for address, param in sorted(pt.items()):
        param_key = param['parameter_key']
        value = values.get(param_key)
        value = byte_table[value]

        size = param['size']
        address = param['address']
        msg_data = parsed_sysex.param_to_send_data(
            device_id, block, address, size, value)
        msg = mido.Message('sysex', data=msg_data)
        if session:
            session.port_out.send(msg)
        else:
            print('%s = %s' % (param_key, value))
            # print(parsed_sysex.ParsedSysex(msg_data))
            # print(msg)
            # io.print_data(msg_data)


class LiveSet(object):

    def __init__(self, conf, data=None):
        self.data = data or EMPTY_LIVESET
        self.conf = conf
        self.patches = collections.OrderedDict()
        for p in self.data['patchList']:
            self._add_patch(p)
        self.data['patchList'] = self.patches.items()

    def _add_patch(self, p):
        key = '%s: %s' % (p.get('orderNumber'), p.get('name').strip())
        self.patches[key] = p

    def add_patch(self, p):
        self._add_patch(p)
        self.data['patchList'] = self.patches.items()

    def to_midi(self, session, patch_key, preset_name=None):
        patch = self.patches[patch_key]
        patch_to_midi(self.conf, session, patch, preset_name)
