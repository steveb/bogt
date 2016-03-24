import logging
import struct

from cliff import command
import mido

from bogt import spec


log = logging.getLogger(__name__)


class ParseData(command.Command):
    '''Parse a MIDI file and print patch values'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ParseData, self).get_parser(prog_name)
        parser.add_argument('filename')
        return parser

    def take_action(self, parsed_args):
        mid = mido.MidiFile(parsed_args.filename)
        parsed = []
        for msg in mid:
            if msg.type != 'sysex':
                continue
            parsed.append(ParsedSysex(msg.data))

        # prev_ps = None
        # parsed_split = []
        for ps in parsed:
            # print('%s == %s' % (ps.checksum, ps.calculate_checksum()))
            print('%s' % ps)
            # parsed_split.extend(ps.split(prev_ps))
            # prev_ps = ps


class ParsedSysex(object):

    def __init__(self, data):
        self.data = data

    @property
    def body(self):
        return self.data[10:-1]

    @property
    def checksum(self):
        return self.data[-1:][0]

    def calculate_checksum(self):
        return 128 - (sum(self.data[6:-1]) % 128)

    @property
    def size(self):
        entry = self.table_entry()
        return entry['size']

    @property
    def address_block(self):
        return struct.unpack(
            '>H', struct.pack(
                'BB', *self.data[6:8]))[0]

    @property
    def address(self):
        return struct.unpack(
            '>I', struct.pack(
                'BBBB', *self.data[6:10]))[0]

    @property
    def table_key(self):
        return struct.unpack(
            '>H', struct.pack(
                'BB', *self.data[8:10]))[0]

    def is_send(self):
        return self.data[5] == 0x12

    def is_receive(self):
        return self.data[5] == 0x11

    def table_entry(self):
        table = spec.table(self.table_name)
        return table[self.table_key]

    def location_label(self):
        try:
            entry = self.table_entry()
        except KeyError:
            log.warn('%s not in %s' % (self.table_key, self.table_name))
            return self.table_key
        parameter = entry['parameter']
        return ': '.join(parameter)

    @property
    def table_name(self):
        block = self.address_block
        if block == 0x0:
            return 'SYSTEM'
        if block == 0x2:
            return 'MIDI'
        return 'PATCH'

    def split(self, prev_ps):
        try:
            entry = self.table_entry()
        except KeyError:
            print('TODO handle prev_ps')
        print(entry)

    def __str__(self):
        sr = '????'
        if self.is_send():
            sr = 'send'
        if self.is_receive():
            sr = 'recv'

        # hexdata = ['%02x' % d for d in self.data]
        # strhexdata = ', '.join(hexdata)
        print(self.location_label())
        return '%s %s %s %s: %s' % (
            sr,
            self.table_name,
            hex(self.address),
            self.checksum,
            len(self.data)
        )
