import logging

from cliff import command
import inquirer

from bogt import config
from bogt import io
from bogt import tsl


class SortPatches(command.Command):
    '''Send one patch at a time and allow sorting to different files'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SortPatches, self).get_parser(prog_name)
        parser.add_argument(
            '--tsl',
            metavar='<from TSL file>',
            help=('Path to source TSL containing patches.')
        )
        parser.add_argument(
            'out',
            nargs='+',
            metavar='<to TSL files...>',
            help=('Path of TSL file to append sorted patches to. Can be '
                  'specified multiple times.')
        )
        # parser.add_argument(
        #     '--remove',
        #     action='store_true',
        #     help=('Remove from source TSL once sorted')
        # )
        parser.add_argument(
            '--no-send',
            action='store_true',
            help=('Do not send MIDI, print debugging to console instead')
        )

        return parser

    def take_action(self, parsed_args):
        conf = config.load_config()
        liveset = tsl.load_tsl_from_file(parsed_args.tsl, conf)
        outs = {out: tsl.load_tsl_from_file(out, conf)
                for out in parsed_args.out}
        for name, patch in liveset.patches.items():
            print(name)
            session = io.Session(conf, fake=parsed_args.no_send)
            liveset.to_midi(session, name)
            out = self.prompt_out(parsed_args.out)
            out_ls = outs[out]
            out_ls.add_patch(patch)
            out_ls.store()

    def prompt_out(self, outs):
        q = [
            inquirer.List(
                'out',
                message="Sort to file",
                default=outs[0],
                choices=outs,
            ),
        ]
        answer = inquirer.prompt(q)
        return answer['out']
