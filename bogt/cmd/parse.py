import logging
import struct

from cliff import command
import mido


class ParseData(command.Command):
    '''Parse a MIDI file and print patch values'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ParseData, self).get_parser(prog_name)
        parser.add_argument('filename')
        return parser

    def take_action(self, parsed_args):
        mid = mido.MidiFile(parsed_args.filename)
        for msg in mid:
            if msg.type == 'sysex':
                ps = ParsedSysex(msg)
                print(ps)


class ParsedSysex(object):

    def __init__(self, msg):
        self.msg = msg
        if msg.type != 'sysex':
            raise ValueError('Not a sysex message')

    @property
    def body(self):
        return self.msg.data[10:-1]

    @property
    def data(self):
        return self.msg.data

    @property
    def checksum(self):
        return self.msg.data[-1:][0]

    @property
    def address_block(self):
        return struct.unpack(
            '>H', struct.pack(
                'BB', *self.msg.data[6:8]))[0]

    @property
    def address(self):
        return struct.unpack(
            '>H', struct.pack(
                'BB', *self.msg.data[8:10]))[0]

    def is_send(self):
        return self.msg.data[5] == 0x12

    def is_receive(self):
        return self.msg.data[5] == 0x11

    def location_label(self):
        return '?'

    @property
    def table_name(self):
        block = self.address_block
        if block < 0x0020:
            return 'SYSTEM'
        if block < 0x1000:
            return 'MIDI'
        return 'PATCH'

    def __str__(self):
        sr = '????'
        if self.is_send():
            sr = 'send'
        if self.is_receive():
            sr = 'recv'

        # hexdata = ['%02x' % d for d in self.data]
        # strhexdata = ', '.join(hexdata)
        return '%s %s %s %s: %s' % (
            sr,
            self.table_name,
            hex(self.address),
            self.checksum,
            len(self.data)
        )
