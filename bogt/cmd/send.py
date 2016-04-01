import logging

from cliff import command


class SendData(command.Command):
    '''Send data from a TSL or MIDI dump file to the device'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SendData, self).get_parser(prog_name)
        parser.add_argument('filename')
        return parser

    def take_action(self, parsed_args):
        return
