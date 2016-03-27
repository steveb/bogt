
import testtools

from bogt import spec


class TestSpec(testtools.TestCase):

    def test_tables(self):
        self.assertEqual(527, len(spec.midi()))
        self.assertEqual(271, len(spec.system()))
        self.assertEqual(882, len(spec.patch()))

    def test_max_table_keys(self):
        self.assertEqual(0x327, spec._max_table_keys['SYSTEM'])
        self.assertEqual(0x87e, spec._max_table_keys['MIDI'])
        self.assertEqual(0x103a, spec._max_table_keys['PATCH'])

    def test_table(self):
        self.assertEqual(2, len(spec.table('USB MIDI')))
        self.assertRaises(ValueError, spec.table, 'USB MOODY')

    def test_table_name(self):
        self.assertEqual('SYSTEM', spec.table_name(0x0))
        self.assertEqual('MIDI', spec.table_name(0x2))
        self.assertEqual('PATCH', spec.table_name(0x2000))
        self.assertRaises(ValueError, spec.table_name, 0x3)

    def test_table_entry(self):
        self.assertEqual('MIDI', spec.table_entry('USB MIDI', 1))
        self.assertRaises(ValueError, spec.table_entry, 'USB MIDI', 2)

    def test_next_table_key(self):
        self.assertEqual(0x11e, spec.next_table_key('PATCH', 0x11e))
        self.assertEqual(0x11f, spec.next_table_key('PATCH', 0x11f))
        self.assertEqual(0x130, spec.next_table_key('PATCH', 0x120))
        self.assertEqual(0x130, spec.next_table_key('PATCH', 0x121))
        self.assertEqual(0x103a, spec.next_table_key('PATCH', 0x103a))
        self.assertRaises(KeyError, spec.next_table_key, 'PATCH', 0x103b)
