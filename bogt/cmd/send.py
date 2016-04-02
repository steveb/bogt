import logging

from cliff import command
import inquirer

from bogt import config
from bogt import tsl


class SendData(command.Command):
    '''Send data from a TSL file to the device'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SendData, self).get_parser(prog_name)
        parser.add_argument('filename')
        return parser

    def take_action(self, parsed_args):
        liveset = tsl.load_tsl_from_file(parsed_args.filename)
        conf = config.load_config()
        last_send = conf.get('last_send', {})

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
            inquirer.List(
                'patch',
                message="Patch to send",
                default=last_send.get('patch'),
                choices=liveset.patches,
            ),
            inquirer.Text(
                'bank',
                message='User bank to write patch to (1 to 50)',
                default=last_send.get('bank'),
                validate=validate_bank
            ),
            inquirer.List(
                'preset',
                message='Preset to write patch to',
                default=last_send.get('preset'),
                choices=build_presets
            ),
        ]
        answer = inquirer.prompt(q)
        conf['last_send'] = answer
        config.save_config(conf)
