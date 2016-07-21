import logging

from cliff import command
import inquirer

from bogt import config
from bogt import tsl


class SortPatches(command.Command):
    '''Send one patch at a time and allow sorting to different files'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SortPatches, self).get_parser(prog_name)
        parser.add_argument(
            'tsl',
            metavar='<from TSL file>',
            help=('Path to TSL file to send patches from.')
        )
        parser.add_argument(
            '--out',
            action='append',
            metavar='<to TSL files...>',
            help=('Path of TSL file to append sorted patches to. Can be '
                  'specified multiple times.')
        )
        parser.add_argument(
            '--no-send',
            action='store_true',
            help=('Do not send MIDI, print debugging to console instead')
        )

        return parser

    def take_action(self, parsed_args):
        conf = config.load_config()
        liveset = tsl.load_tsl_from_file(parsed_args.tsl, conf)
        answer = self.prompt_patch({}, liveset.patches)
        patch = answer['patch']

        preset = None
        print(parsed_args.out)
        # if parsed_args.write:
        #     answer = self.prompt_preset(last_send)
        #     preset = answer['preset']

        # config.save_config(conf)
        # if parsed_args.no_send:
        #     session = None
        # else:
        #     session = io.Session(conf)
        # liveset.to_midi(session, patch, preset)

    def prompt_patch(self, last_send, patches):
        q = [
            inquirer.List(
                'patch',
                message="Patch to send",
                default=last_send.get('patch'),
                choices=patches,
            ),
        ]
        answer = inquirer.prompt(q)
        last_send.update(answer)
        return answer
