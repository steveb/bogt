
import os
import struct
import testtools

import mido

from bogt import parsed_sysex
from bogt import spec

test_dir = os.path.dirname(__file__)
test_path_1 = os.path.join(test_dir, 'test_parsed_sysex_1.mid')
test_path_2 = os.path.join(test_dir, 'test_parsed_sysex_2.mid')


class TestParseFunctions(testtools.TestCase):

    def test_checksum_with_data(self):
        self.assertEqual(0,
                         parsed_sysex.checksum_with_data([]))
        self.assertEqual(127,
                         parsed_sysex.checksum_with_data([1]))
        self.assertEqual(122,
                         parsed_sysex.checksum_with_data([1, 2, 3]))
        self.assertEqual(64,
                         parsed_sysex.checksum_with_data([0, 0, 64]))

    def test_bytes_to_ushort(self):
        self.assertEqual(
            0x1234,
            parsed_sysex.bytes_to_ushort([0x12, 0x34]))
        self.assertEqual(
            0x0,
            parsed_sysex.bytes_to_ushort([0x0, 0x0]))
        self.assertRaises(
            struct.error,
            parsed_sysex.bytes_to_ushort,
            [0x0])
        self.assertRaises(
            struct.error,
            parsed_sysex.bytes_to_ushort,
            [0x0, 0x1, 0x2])

    def test_bytes_to_uint(self):
        self.assertEqual(
            0x1234abcd,
            parsed_sysex.bytes_to_uint([0x12, 0x34, 0xab, 0xcd]))
        self.assertEqual(
            0x0,
            parsed_sysex.bytes_to_uint([0x0, 0x0, 0x0, 0x0]))
        self.assertRaises(
            struct.error,
            parsed_sysex.bytes_to_uint,
            [0x0])
        self.assertRaises(
            struct.error,
            parsed_sysex.bytes_to_uint,
            [0x0, 0x1, 0x2, 0x3, 0x4])

    def test_ushort_to_bytes(self):
        self.assertEqual(
            (0x12, 0x34),
            parsed_sysex.ushort_to_bytes(0x1234))
        self.assertEqual(
            (0x0, 0x0),
            parsed_sysex.ushort_to_bytes(0x0))

    def test_uint_to_bytes(self):
        self.assertEqual(
            (0x00, 0x00, 0xab, 0xcd),
            parsed_sysex.uint_to_bytes(0xabcd))
        self.assertEqual(
            (0x12, 0x34, 0xab, 0xcd),
            parsed_sysex.uint_to_bytes(0x1234abcd))
        self.assertEqual(
            (0x0, 0x0, 0x0, 0x0),
            parsed_sysex.uint_to_bytes(0x0))


class TestParsedSysex(testtools.TestCase):

    def test_parsed(self):
        mid = mido.MidiFile(test_path_1)
        parsed = parsed_sysex.midi_to_parsed(mid, split=False)
        self.assertEqual(9, len(parsed))

    def test_parsed_split_1(self):
        mid = mido.MidiFile(test_path_1)
        parsed = parsed_sysex.midi_to_parsed(mid, split=True)
        self.assertEqual(len(spec.patch()), len(parsed))

    def test_parsed_split_2(self):
        mid = mido.MidiFile(test_path_2)
        parsed = parsed_sysex.midi_to_parsed(mid, split=True)
        self.assertEqual(len(spec.patch()), len(parsed))
