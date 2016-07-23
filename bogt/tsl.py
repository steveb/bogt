
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
        self.data['patchList'] = self.patches.values()

    def _add_patch(self, p):
        key = '%s: %s' % (p.get('orderNumber'), p.get('name').strip())
        self.patches[key] = p

    def add_patch(self, p):
        self._add_patch(p)
        self.data['patchList'] = self.patches.values()

    def to_midi(self, session, patch_key, preset_name=None):
        patch = self.patches[patch_key]
        patch_to_midi(self.conf, session, patch, preset_name)

    def to_file(self, path):
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def write_patch_order(self, patch, info_out):
        fx_chain = spec.table('FX CHAIN')
        start_fx = []
        end_fx = []
        a_fx = []
        b_fx = []
        positions = patch['params']['chainParams']['positionList']
        state = 'start'
        for p in positions:
            fx = fx_chain[p]
            if fx == 'DIV1':
                state = 'a'
                continue
            elif fx == 'MIX1_DIV2':
                state = 'b'
                continue
            elif fx == 'MIX2':
                state = 'end'
                continue
            if state == 'start':
                start_fx.append(fx)
            elif state == 'a':
                a_fx.append(fx)
            elif state == 'b':
                b_fx.append(fx)
            elif state == 'end':
                end_fx.append(fx)

        info_out.write('             |\n')
        for fx in start_fx:
            info_out.write('        %s\n' % fx.center(12))
            info_out.write('             |\n')
        info_out.write('       ------------ \n')
        info_out.write('      |            |\n')
        for i in range(max(len(a_fx), len(b_fx))):
            afx = a_fx and a_fx.pop(0) or None
            bfx = b_fx and b_fx.pop(0) or None
            if afx:
                info_out.write(' %s' % afx.center(12))
            else:
                info_out.write('      |     ')
            if bfx:
                info_out.write(' %s\n' % bfx.center(12))
            else:
                info_out.write('       |     \n')
            info_out.write('      |            |\n')
        info_out.write('       ------------ \n')
        info_out.write('             |\n')
        for fx in end_fx:
            info_out.write('        %s\n' % fx.center(12))
            info_out.write('             |\n')
