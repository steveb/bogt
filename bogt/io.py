
import sys

import mido


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


class Session(object):

    def __init__(self, conf):
        self.conf = conf
        set_backend(conf)
        self.port_in = mido.open_input(conf['port_in'])
        self.port_out = mido.open_output(conf['port_out'])

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
