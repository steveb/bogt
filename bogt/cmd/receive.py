import logging
import sys

from cliff import command
import inquirer

from bogt import config
from bogt import io
from bogt import tsl


class ReceiveData(command.Command):
    '''Receive a MIDI data dump and save to file'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ReceiveData, self).get_parser(prog_name)
        parser.add_argument(
            'tsl',
            metavar='<TSL file>',
            help=('Path to TSL file to append to.')
        )
        parser.add_argument(
            '--preset',
            action='store_true',
            help=('Prompt for preset to read from instead of temporary memory')
        )
        return parser

    def take_action(self, parsed_args):
        conf = config.load_config()

        preset = None
        if parsed_args.preset:
            last_receive = conf.get('last_receive', {})
            answer = self.prompt_preset(last_receive)
            preset = answer['preset']
        session = io.Session(conf)
        patch = session.receive_preset(preset)
        tsl.write_patch_order(patch, sys.stdout)
        liveset = tsl.load_tsl_from_file(parsed_args.tsl, conf)
        liveset.add_patch(patch)
        liveset.store()

    def prompt_preset(self, last_receive):
        def validate_bank(answers, value):
            try:
                i = int(value)
                return i > 0 and i < 51
            except ValueError:
                return False

        def build_presets(answers):
            bank = 'U%02d' % int(answers['bank'])
            return ['%s-%s' % (bank, i) for i in range(1, 5)]

        q = [
            inquirer.Text(
                'bank',
                message='User bank to read patch from (1 to 50)',
                default=last_receive.get('bank'),
                validate=validate_bank
            ),
            inquirer.List(
                'preset',
                message='Preset to read patch from',
                default=last_receive.get('preset'),
                choices=build_presets
            ),
        ]
        answer = inquirer.prompt(q)
        last_receive.update(answer)
        return answer
