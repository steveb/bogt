
import collections
import random
import sys

import mido

from bogt import parsed_sysex as ps
from bogt import spec


def set_backend(conf=None):
    if not conf:
        conf = {}
    backend = conf.get('backend', 'mido.backends.rtmidi')
    api = conf.get('api')
    if api:
        mido.set_backend('%s/%s' % (backend, api))
    else:
        mido.set_backend(backend)


def get_available_apis():
    '''A list of compiled MIDI APIs'''
    set_backend()
    return mido.backend.module.get_api_names()


def get_input_ports():
    return mido.get_input_names()


def get_output_ports():
    return mido.get_output_names()


def print_data(data):
    sys.stdout.write('[')
    for d in data:
        sys.stdout.write(hex(d))
        sys.stdout.write(', ')
    sys.stdout.write(']\n')


def build_param_send_msg(device_id, block, address, size, value):
    data = [
        0x41,       # Manufacturer ID (Roland)
        device_id,  # Dev Device ID (Dev=00H-1FH)
        0x00,       # Model ID #1 (GT-100)
        0x00,       # Model ID #2 (GT-100)
        0x60,       # Model ID #3 (GT-100)
        0x12        # Command ID (DT1)
    ]
    data.extend(ps.ushort_to_bytes(block))
    data.extend(ps.ushort_to_bytes(address))
    if size == 1:
        data.append(value)
    elif size == 2:
        data.extend(ps.ushort_to_bytes(value))
    data.append(ps.checksum_with_data(data[6:]))
    return data


def build_request_data_msg(device_id, block, address, size):
    data = [
        0x41,       # Manufacturer ID (Roland)
        device_id,  # Dev Device ID (Dev=00H-1FH)
        0x00,       # Model ID #1 (GT-100)
        0x00,       # Model ID #2 (GT-100)
        0x60,       # Model ID #3 (GT-100)
        0x11        # Command ID (RQ1)
    ]
    data.extend(ps.ushort_to_bytes(block))
    data.extend(ps.ushort_to_bytes(address))
    data.extend(ps.uint_to_bytes(size))
    data.append(ps.checksum_with_data(data[6:]))
    return data


def populate_chain_params(patch):
    param_data = patch['params']
    pos_list = []
    chain_params = {'positionList': pos_list}
    for i in range(1, 21):
        key = 'fx_chain_position%d' % i
        pos_key = 'position%d' % i
        value = param_data[key]
        chain_params[pos_key] = value
        pos_list.append(value)
    param_data['chainParams'] = chain_params


def populate_name(patch):
    param_data = patch['params']
    name = ''
    for i in range(1, 16):
        key = 'patch_name%d' % i
        name += chr(param_data[key])
    param_data['patchname'] = name.strip()
    patch['name'] = name
    patch['gt100Name1'] = name[:8]
    patch['gt100Name2'] = name[8:]


def populate_category(patch):
    category_value = patch['params']['patch_category']
    category_table = spec.table('Patch Category')
    category = category_table.get(category_value)
    patch['category'] = category


def populate_unused_fields(patch):
    patch['patchID'] = None
    patch['patchNo'] = None,
    patch['tcPatch'] = False
    patch['logPatchName'] = None
    patch['note'] = ''


class Session(object):

    port_in = None
    port_out = None

    def __init__(self, conf, fake=False):
        self.conf = conf
        if not fake:
            set_backend(conf)
            self.port_in = mido.open_input(conf['port_in'])
            self.port_out = mido.open_output(conf['port_out'])

    def receive_preset(self, preset_name):
        if not preset_name:
            preset_name = "TEMPORARY PATCH"
        upb = spec.table('USER PATCH BLOCK REVERSE')
        byte_table = spec.table('BYTENUM TO INDEX REVERSE')
        block = upb[preset_name]
        param_data = {}
        patch = {
            'id': '%010d' % random.randint(1, 9999999999),
            'params': param_data
        }

        patch_table = spec.patch()
        device_id = self.conf.get('device_id', 0x00)

        def is_data_set(resp):
            if resp.type != 'sysex':
                return False

            prefix = list(resp.data[:6])
            match = [0x41, prefix[1], 0x0, 0x0, 0x60, 0x12]
            return match == prefix

        # drain any pending data, we don't need it
        all(self.port_in.iter_pending())

        # request in chunks of MSB resolution, maximum 128 bytes per chunk
        msb_map = collections.defaultdict(list)
        for address, param in sorted(patch_table.items()):
            msb = address >> 8
            msb_map[msb].append(param)

        for msb, params in sorted(msb_map.items()):
            address = params[0]['address']
            end_address = params[-1]['address'] + params[-1]['size']
            size = end_address - address
            msg_data = build_request_data_msg(
                device_id, block, address, byte_table[size])
            msg = mido.Message('sysex', data=msg_data)
            self.port_out.send(msg)

            resp = self.port_in.receive()
            if not is_data_set(resp):
                raise Exception('Expected DataSet response')
            full_address_response = ps.bytes_to_uint(resp.data[6:10])
            full_address = (block << 16) + address
            if full_address_response != full_address:
                raise Exception('Asked for address %s, got address %s' % (
                                hex(full_address), hex(full_address_response)))
            # data is after the address, and before the checksum
            data = resp.data[10:-1]
            if len(data) != size:
                raise Exception('Expected %s bytes, got %s' % (size,
                                                               len(data)))
            for param in params:
                index = param['address'] - address
                param_key = param['parameter_key']
                if param['size'] == 1:
                    value = ps.bytes_to_uchar(data[index:index + 1])
                else:
                    value = ps.bytes_to_ushort(data[index:index + 2])
                param_data[param_key] = value
                # lookup_name = param['lookup']
                # lookup_table = spec.table(lookup_name)
                # if lookup_table:
                #     display_value = spec.table(lookup_name)[value]
                # else:
                #     display_value = value
                # print('%s=%s' % (param['parameter_key'], display_value))
        populate_chain_params(patch)
        populate_name(patch)
        populate_category(patch)
        populate_unused_fields(patch)
        return patch

    def patch_to_midi(self, patch, preset_name):
        values = patch['params']
        if not preset_name:
            preset_name = "TEMPORARY PATCH"

        upb = spec.table('USER PATCH BLOCK REVERSE')
        byte_table = spec.table('BYTENUM TO INDEX REVERSE')
        block = upb[preset_name]
        device_id = self.conf.get('device_id', 0x00)
        pt = spec.patch()
        for address, param in sorted(pt.items()):
            param_key = param['parameter_key']
            value = values.get(param_key)
            value = byte_table[value]

            size = param['size']
            address = param['address']
            msg_data = build_param_send_msg(
                device_id, block, address, size, value)
            msg = mido.Message('sysex', data=msg_data)
            if self.port_out:
                self.port_out.send(msg)
            # else:
            #     print('%s = %s' % (param_key, value))
                # print(ps.ParsedSysex(msg_data))
                # print(msg)
                # io.print_data(msg_data)

    def query_device_info(self):
        data = [
            0x7e,  # ID number (Universal Non-realtime Message)
            0x7f,  # Device ID (all devices)
            0x06,  # Sub ID#1 (General Information)
            0x01   # Sub ID#2 (Identity Request)
        ]
        msg = mido.Message('sysex', data=data)
        self.port_out.send(msg)

        def is_identity_reply(resp):
            if resp.type != 'sysex':
                return False

            prefix = list(resp.data[:4])
            match = [0x7e, prefix[1], 0x06, 0x02]
            return match == prefix

        while True:
            resp = self.port_in.receive()
            if not is_identity_reply(resp):
                continue
            if resp.data[4] != 0x41:
                print('Ignoring unknown manufacturer %s' % hex(resp.data[4]))
                continue
            family_code = resp.data[5:7]
            device_id = resp.data[1]
            if family_code == (0x60, 0x02):
                return device_id, 'GT-100'
            if family_code == (0x60, 0x03):
                return device_id, 'GT-001'
            print('Ignoring unknown family code %s %s' % (
                hex(family_code[0]), hex(family_code[1])))
