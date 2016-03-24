
import testtools

from bogt import spec


class TestSpec(testtools.TestCase):

    def test_tables(self):
        self.assertEqual(526, len(spec.midi()))
        self.assertEqual(270, len(spec.system()))
        self.assertEqual(881, len(spec.patch()))

    def test_table_name(self):
        self.assertEqual(2, len(spec.table('USB MIDI')))
        self.assertRaises(ValueError, spec.table, 'USB MOODY')

    def test_table_entry(self):
        self.assertEqual('MIDI', spec.table_entry('USB MIDI', 1))
        self.assertRaises(ValueError, spec.table_entry, 'USB MIDI', 2)
