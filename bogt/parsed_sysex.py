import logging
import struct

from bogt.io import print_data
from bogt import spec

log = logging.getLogger(__name__)


def midi_to_parsed(midi, split=False):
    parsed = []
    for msg in midi:
        if msg.type != 'sysex':
            continue
        parsed.append(ParsedSysex(msg.data))
    if not split:
        return parsed

    merged_ps = merge_parsed(parsed)
    parsed_split = []
    merged_ps.split(parsed_split)
    for ps in parsed_split:
        # print_data(ps.data)
        print(ps)
    return parsed_split


def merge_parsed(parsed):
    if len(parsed) < 2:
        return parsed
    merge_ps = parsed[0]
    for ps in parsed[1:]:
        merge_ps = merge_ps.create_by_merging(ps)
    return merge_ps


def checksum_with_data(data):
    return 128 - (sum(data) % 128)


def bytes_to_uchar(data):
    return data[0]


def bytes_to_ushort(data):
    return struct.unpack(
        '>H', struct.pack(
            'BB', *data))[0]


def bytes_to_uint(data):
    return struct.unpack(
        '>I', struct.pack(
            'BBBB', *data))[0]


def ushort_to_bytes(data):
    return struct.unpack('BB', struct.pack('>H', data))


def uchar_to_bytes(data):
    return [data]


def uint_to_bytes(data):
    return struct.unpack('BBBB', struct.pack('>I', data))


class ParsedSysex(object):

    def __init__(self, data):
        self.populate_from_data(data)
        self.populate_from_table()

    def populate_from_data(self, data):
        self.data = data

        self.is_send = self.data[5] == 0x12
        self.is_receive = self.data[5] == 0x11
        self.address = bytes_to_uint(self.data[6:10])
        self.address_block = bytes_to_ushort(self.data[6:8])
        self.table_key = bytes_to_ushort(self.data[8:10])
        self.body = self.data[10:-1]
        self.checksum = self.data[-1:][0]
        self.table_name = spec.table_name(self.address_block)

    def populate_from_table(self):

        try:
            self.table = spec.table(self.table_name)
            self.table_entry = self.table[self.table_key]
            self.size = self.table_entry['size']
            self.lookup_value_data = self.body[:self.size]
            self.table_entry_label = ': '.join(self.table_entry['parameter'])
            if len(self.lookup_value_data) != self.size:
                print('WARNING missing value data %s %s' % (
                    self.size, self.data))
            else:
                if self.size == 1:
                    self.lookup_value = bytes_to_uchar(self.lookup_value_data)
                elif self.size == 2:
                    self.lookup_value = bytes_to_ushort(self.lookup_value_data)
                elif self.size == 4:
                    self.lookup_value = bytes_to_uint(self.lookup_value_data)
                else:
                    raise ValueError('Unhandled size: %s' % self.size)
        except KeyError:
            self.table = None
            self.table_entry = None
            self.size = None
            self.table_entry_label = self.table_key
            self.lookup_value = None

        if not self.table_entry:
            return
        try:
            self.lookup_table = spec.table(self.table_entry['lookup'])
            self.lookup_value_label = self.lookup_table[self.lookup_value]
        except KeyError:
            self.lookup_table = None
            self.lookup_value_label = None

    def create_by_truncate(self):
        if not self.size:
            print('NO TABLE ENTRY %s' % hex(self.address))
            return None, None
        size_minus_checksum = 10 + self.size
        d = list(self.data[:size_minus_checksum])
        d.append(checksum_with_data(d[6:]))
        data_remains = self.data[size_minus_checksum:]
        ps = ParsedSysex(d)
        return ps, data_remains

    def create_by_data_remains(self, data_remains):
        next_address_block = self.address_block
        try:
            next_table_key = spec.next_table_key(
                self.table_name, self.table_key + self.size)
        except KeyError:
            return None
        try:
            next_size = spec.table_entry(
                self.table_name, next_table_key)['size']
        except ValueError:
            return None
        if data_remains <= next_size + 1:
            # not enough data to create a full packet
            return None

        d = list(self.data[:6])
        d.extend(ushort_to_bytes(next_address_block))
        d.extend(ushort_to_bytes(next_table_key))
        d.extend(data_remains[:-1])
        d.append(checksum_with_data(d[6:]))
        ps = ParsedSysex(d)
        return ps

    def create_by_merging(self, ps):
        d = list(self.data[:10])
        d.extend(self.body)
        d.extend(ps.body)
        d.append(checksum_with_data(d[6:]))
        return ParsedSysex(d)

    def split(self, parsed_split):
        large_ps = self
        while True:
            ps, data_remains = large_ps.create_by_truncate()
            if not ps:
                return
            parsed_split.append(ps)
            if len(data_remains) < 2:
                # if all that is left is the checksum
                return
            # print(data_remains)
            large_ps = large_ps.create_by_data_remains(data_remains)
            if not large_ps:
                print('dangling data')
                print_data(data_remains)
                return

    def calculate_checksum(self, data):
        return self.checksum_with_data(self.data[6:-1])

    def __str__(self):
        return '%s: %s\n%s = %s' % (
            hex(self.address),
            self.body[:self.size],
            self.table_entry_label,
            self.lookup_value_label
        )
