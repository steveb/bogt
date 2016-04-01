import logging

from cliff import command
import json
import mido

from bogt import parsed_sysex
from bogt import parsed_tsl


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
        parsed = parsed_sysex.midi_to_parsed(mid, split=False)
        for ps in parsed:
            self.app.stdout.write('%s\n' % ps)


class TslToMidi(command.Command):
    '''Parse a TSL file and write out a MIDI file'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(TslToMidi, self).get_parser(prog_name)
        parser.add_argument('tsl_filename')
        parser.add_argument('midi_filename')
        return parser

    def take_action(self, parsed_args):
        with open(parsed_args.tsl_filename) as f:
            tsl_data = json.load(f)
            parsed_tsl.create_from_data(tsl_data)
            with open(parsed_args.midi_filename, 'w') as fo:
                parsed_tsl.write_midi(fo)
