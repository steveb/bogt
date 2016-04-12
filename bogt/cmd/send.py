import logging
import os
import sqlite3

from cliff import command
import inquirer

from bogt import bts_db
from bogt import config
from bogt import tsl


class SendData(command.Command):
    '''Send data from a TSL file to the device'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SendData, self).get_parser(prog_name)
        parser.add_argument(
            '--tls',
            metavar='<file>',
            help=('Path to TLS file to select patch from. '
                  'If not specified, will '
                  'load configured BOSS TONE STUDIO database.')
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help=('Watch for data changes and resend patch')
        )

        return parser

    def take_action(self, parsed_args):
        if parsed_args.tls:
            self.take_action_tls(parsed_args)
        else:
            self.take_action_bts_db(parsed_args)

    def take_action_bts_db(self, parsed_args):
        conf = config.load_config()
        last_send = conf.get('last_send', {})
        db = bts_db.BtsDb(conf)
        liveset_names = db.fetch_liveset_names()
        q = [
            inquirer.List(
                'liveset',
                message="Liveset to get patch from",
                default=last_send.get('liveset'),
                choices=liveset_names,
            ),
        ]
        answer = inquirer.prompt(q)
        liveset_id = liveset_names[answer['liveset']]
        patch_names = db.fetch_patch_names(liveset_id)
        answer = self.prompt_preset(last_send, patch_names)
        patch_id = patch_names[answer['patch']]
        patch = db.fetch_patch(patch_id)
        tsl.patch_to_midi(conf, patch, answer['preset'])

    def take_action_tls(self, parsed_args):
        conf = config.load_config()
        liveset = tsl.load_tsl_from_file(parsed_args.tls, conf)
        last_send = conf.get('last_send', {})
        answer = self.prompt_preset(last_send, liveset.patches)
        conf['last_send'] = answer
        config.save_config(conf)
        liveset.to_midi(answer['patch'], answer['preset'])

    def prompt_preset(self, last_send, patches):
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
                choices=patches,
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
        return answer
