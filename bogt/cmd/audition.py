import logging
import os
import time

from cliff import command
from slugify import slugify
import wavefile

from bogt import config
from bogt import io
from bogt import tsl


class Audition(command.Command):
    '''Audition all patches in a TSL by playing and recording a sample'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Audition, self).get_parser(prog_name)
        parser.add_argument(
            'tsl',
            metavar='<TSL file>',
            help=('Path to TSL file to send patches from.')
        )
        parser.add_argument(
            '--sample',
            metavar='<audio file>',
            required=True,
            help=('Path of audio file to play for each patch')
        )
        parser.add_argument(
            '--dest',
            metavar='<directory path>',
            help=('Path of directory to save audio files to. Will create if '
                  'it does not exist.')
        )
        parser.add_argument(
            '--no-record',
            action='store_true',
            help=('Do not record and save results')
        )
        parser.add_argument(
            '--no-send',
            action='store_true',
            help=('Do not send MIDI, print debugging to console instead')
        )

        return parser

    def take_action(self, parsed_args):
        self.conf = config.load_config()
        self.tsl = os.path.abspath(parsed_args.tsl)
        if not os.path.exists(self.tsl) or not os.path.isfile(self.tsl):
            raise Exception('TSL file not found: %s' % self.tsl)
        self.tsl_name = os.path.splitext(os.path.basename(self.tsl))[0]

        self.no_record = parsed_args.no_record
        if not parsed_args.no_record:
            if parsed_args.dest:
                dest = parsed_args.dest
            else:
                dest = '%s.d' % parsed_args.tsl
            self.dest = self.prep_dest(dest)
        self.liveset = tsl.load_tsl_from_file(parsed_args.tsl, self.conf)
        sr, d = wavefile.load(parsed_args.sample)
        self.sample_rate = sr
        self.play_data = d.T
        self.session = io.Session(self.conf, fake=parsed_args.no_send)
        self.audition()

    def prep_dest(self, dest):
        dest = os.path.abspath(dest)
        if not os.path.isdir(dest):
            if os.path.exists(dest):
                raise Exception('dest exists and is not a directory: %s' %
                                dest)
            else:
                os.makedirs(dest)
        return dest

    def audition(self):
        for name, patch in self.liveset.patches.items():
            self.patch_name = '%s-%s' % (self.tsl_name, name)
            self.patch_name_clean = slugify(self.patch_name)
            print(self.patch_name_clean)
            self.liveset.to_midi(self.session, name, None)
            # allow the patch change to settle
            time.sleep(1)
            if self.no_record:
                self.play()
            else:
                rec_data = self.playrec()
                self.save_audio(rec_data)
            # allow the audio to settle
            time.sleep(1)

    def playrec(self):
        import sounddevice as sd
        sd.default.channels = 2
        sd.default.samplerate = self.sample_rate
        rec = sd.playrec(self.play_data, self.sample_rate)
        sd.wait()
        return rec.T

    def play(self):
        import sounddevice as sd
        sd.default.channels = 2
        sd.default.samplerate = self.sample_rate
        sd.play(self.play_data, self.sample_rate)
        sd.wait()

    def save_audio(self, rec_data):
        filename = '%s.wav' % self.patch_name_clean
        filepath = os.path.join(self.dest, filename)
        channels, frames = rec_data.shape
        with wavefile.WaveWriter(filepath,
                                 channels=channels,
                                 samplerate=self.sample_rate) as w:
            w.write(rec_data)
