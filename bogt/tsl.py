
import collections
import json

import mido

from bogt import io  # noqa
from bogt import parsed_sysex
from bogt import spec


def load_tsl_from_file(path, conf):
    with open(path) as f:
        return LiveSet(json.load(f), conf)


class LiveSet(object):

    def __init__(self, data, conf):
        self.data = data
        self.conf = conf
        self.patches = collections.OrderedDict()
        for p in data.get('patchList', []):
            key = '%s: %s' % (p.get('orderNumber'), p.get('name').strip())
            self.patches[key] = p

    def to_midi(self, patch_key, preset_name):
        patch = self.patches[patch_key]
        values = patch['params']
        upb = spec.table('USER PATCH BLOCK REVERSE')
        byte_table = spec.table('BYTENUM TO INDEX REVERSE')
        block = upb[preset_name]
        device_id = self.conf.get('device_id', 0x00)
        pt = spec.patch()
        for address, param in sorted(pt.items()):
            param_key = param['parameter_key']
            value = values[param_key]
            value = byte_table[value]

            print('\n%s = %s' % (param_key, value))
            size = param['size']
            address = param['address']
            msg_data = parsed_sysex.param_to_send_data(
                device_id, block, address, size, value)
            print(parsed_sysex.ParsedSysex(msg_data))
            io.print_data(msg_data)
            msg = mido.Message('sysex', data=msg_data)
            print(msg)
