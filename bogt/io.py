
import collections
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


class Session(object):

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
        index_table = spec.table('BYTENUM TO INDEX')
        block = upb[preset_name]

        patch_table = spec.patch()
        device_id = self.conf.get('device_id', 0x00)

        def is_data_set(resp):
            if resp.type != 'sysex':
                return False

            prefix = list(resp.data[:6])
            match = [0x41, prefix[1], 0x0, 0x0, 0x60, 0x12]
            return match == prefix

        # drain any pending data
        all(self.port_in.iter_pending())
        msb_map = collections.defaultdict(list)

        for address, param in sorted(patch_table.items()):
            msb = address >> 8
            msb_map[msb].append(param)

        for msb, params in sorted(msb_map.items()):
            address = params[0]['address']
            end_address = params[-1]['address'] + params[-1]['size']
            print('%s %s->%s' % (hex(msb), hex(address),
                                 hex(end_address)))
            size = end_address - address
            print('address: %s size: %s' % (address, size))
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
                print(param['parameter_key'])
                index = param['address'] - address
                if param['size'] == 1:
                    value = ps.bytes_to_uchar(data[index:index + 1])
                else:
                    value = ps.bytes_to_ushort(data[index:index + 2])
                print('%s=%s' % (param['parameter_key'], value))

        # while True:
            # resp = self.port_in.receive()
            # if not is_data_set(resp):
            #     continue
            # address = ps.bytes_to_uint(resp.data[6:10])
            # print('address: %s' % hex(address))
            # data = resp.data[10:]
            # print('data length: %s' % hex(len(data)))
            # received_data.extend(resp.data[10:])
            # print('total so far: %s' % (hex(len(received_data))))
            # for d in resp.data[10:]:
            #     print('%s = %s' % (hex(address), hex(d)))
            #     address = address + 1

            # if resp.data[4] != 0x41:
            #     print('Ignoring unknown manufacturer %s' % hex(resp.data[4]))
            #     continue
            # family_code = resp.data[5:7]
            # device_id = resp.data[1]
            # if family_code == (0x60, 0x02):
            #     return device_id, 'GT-100'
            # if family_code == (0x60, 0x03):
            #     return device_id, 'GT-001'
            # print('Ignoring unknown family code %s %s' % (
            #     hex(family_code[0]), hex(family_code[1])))

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
            else:
                print('%s = %s' % (param_key, value))
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
