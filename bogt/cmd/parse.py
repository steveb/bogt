import logging

from cliff import command
import mido

from bogt import io
from bogt import parsed_sysex


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
            io.print_data(ps.data[:10])
            self.app.stdout.write('%s\n' % ps)
