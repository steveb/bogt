import logging

from cliff import command
import inotify_simple
import inquirer

from bogt import config
from bogt import io
from bogt import tsl


class SendData(command.Command):
    '''Send data from a TSL file to the device'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(SendData, self).get_parser(prog_name)
        parser.add_argument(
            'tsl',
            metavar='<TSL file>',
            help=('Path to TSL file to select patch from.')
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help=('Watch for data changes and resend patch')
        )
        parser.add_argument(
            '--preset',
            action='store_true',
            help=('Prompt for preset to write to instead of temporary memory')
        )
        parser.add_argument(
            '--no-send',
            action='store_true',
            help=('Do not send MIDI, print debugging to console instead')
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help=('Fetch the patch after sending and confirm correct values')
        )

        return parser

    def watch(self, file_path, get_patch, preset):
        inotify = inotify_simple.INotify()
        f = inotify_simple.flags
        watch_flags = f.ACCESS | f.MODIFY
        inotify.add_watch(file_path, watch_flags)
        while True:
            for event in inotify.read():
                print(event)
                for flag in f.from_mask(event.mask):
                    print('    ' + str(flag))

    def take_action(self, parsed_args):
        conf = config.load_config()
        self.liveset = tsl.load_tsl_from_file(parsed_args.tsl, conf)
        last_send = conf.get('last_send', {})
        answer = self.prompt_patch(last_send, self.liveset.patches)
        patch = answer['patch']

        preset = None
        if parsed_args.preset:
            answer = self.prompt_preset(last_send)
            preset = answer['preset']

        config.save_config(conf)
        self.session = io.Session(conf, fake=parsed_args.no_send)
        self.liveset.to_midi(self.session, patch, preset)

        conf['last_send'] = last_send
        if parsed_args.verify:
            self.verify(patch, preset)

    def verify(self, patch, preset):
        local_data = self.liveset.patches[patch]['params']
        fetched_data = self.session.receive_preset(preset)['params']
        ignore_params = (
            'currentPatchNo', 'pitch_detection', 'prevCurrentPatchNo'
        )
        fail_count = 0
        for k, v in sorted(local_data.items()):
            if k in ignore_params:
                continue
            # ignore gui knob range limits
            if k[-2:] in ('_l', '_h'):
                continue
            fv = fetched_data.get(k)
            if v != fv:
                print('%s = %s, expected %s' % (k, fv, v))
                fail_count += 1
        if not fail_count:
            print('All values correct!')

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

    def prompt_preset(self, last_send):
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
        last_send.update(answer)
        return answer
