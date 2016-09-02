
import collections
import copy
import json
import os

from bogt import io  # noqa
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
    if os.path.isfile(path):
        with open(path) as f:
            return LiveSet(conf, json.load(f), path=path)
    if os.path.exists(path):
        raise Exception('%s is not a file' % path)
    return LiveSet(conf, path=path)


def write_patch_order(patch, info_out):
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


class LiveSet(object):

    def __init__(self, conf, data=None, path=None):
        self.data = data or dict(EMPTY_LIVESET)
        self.conf = conf
        self.path = path
        self.patches = collections.OrderedDict()
        for p in self.data['patchList']:
            self._add_patch(p)
        self._sync_data()

    def _add_patch(self, p):
        order_num = len(self.patches) + 1
        p['orderNumber'] = order_num
        key = '%s: %s' % (order_num, p.get('name').strip())
        self.patches[key] = p
        return key

    def _sync_data(self):
        self.data['patchList'] = self.patches.values()

    def add_patch(self, p):
        key = self._add_patch(copy.deepcopy(p))
        self._sync_data()
        return key

    def remove_patch(self, patch_key):
        del self.patches[patch_key]
        i = 1
        for p in self.patches.itervalues():
            p['orderNumber'] = i
            i += 1
        self._sync_data()

    def to_midi(self, session, patch_key, preset_name=None):
        patch = self.patches[patch_key]
        session.patch_to_midi(patch, preset_name)

    def store(self):
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)
