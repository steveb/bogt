import logging

from cliff import command


class ReceiveData(command.Command):
    '''Receive a MIDI data dump and save to file'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ReceiveData, self).get_parser(prog_name)
        parser.add_argument('filename')
        return parser

    def take_action(self, parsed_args):
        return
