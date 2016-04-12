import logging
import os

from cliff import command
import inquirer

from bogt import config
from bogt import io

log = logging.getLogger('__name__')


class Configure(command.Command):
    '''Query midi devices and prompt questions to create a config file'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Configure, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        conf = config.load_config()
        if self.prompt_doit('Configure MIDI ports?'):
            self.prompt_api(conf)
            io.set_backend(conf)
            self.prompt_ports(conf)
            config.save_config(conf)

        if self.prompt_doit('Configure device by connecting to it?'):
            self.find_device(conf)
            config.save_config(conf)

        if self.prompt_doit('Find BOSS TONE STUDIO database?'):
            self.find_bts_db(conf)
            config.save_config(conf)

    def find_bts_db(self, conf):
        search_path = conf.get('bts_db_dir')
        if not search_path or not os.path.exists(search_path):
            search_path = os.path.expanduser('~/.PlayOnLinux')
        if not os.path.isdir(search_path):
            search_path = os.path.expanduser('~/.wine')
        if not os.path.isdir(search_path):
            search_path = os.path.expanduser('~')

        q = [
            inquirer.Text(
                'search_path',
                message='Path to search for BOSS TONE STUDIO Application Data',
                default=search_path
            ),
        ]
        answer = inquirer.prompt(q)
        search_path = answer['search_path']
        print('Looking for liveset.db in %s...' % search_path)
        for root, dirnames, filenames in os.walk(search_path):
            if 'liveset.db' in filenames:
                print('Found liveset.db in %s' % root)
                conf['bts_db_dir'] = root
                return

    def prompt_doit(self, prompt):
        q = [inquirer.Confirm(
            'doit',
            default=True,
            message=prompt)]
        answer = inquirer.prompt(q)
        return answer['doit']

    def find_device(self, conf):
        print('Looking for device. Ctrl-c if this takes too long...')
        sess = io.Session(conf)
        device_id, family_code = sess.query_device_info()
        conf['device_id'] = device_id
        conf['family_code'] = family_code

    def prompt_api(self, conf):
        apis = io.get_available_apis()
        q = [inquirer.List(
            'api',
            default=conf.get('api'),
            message="Which MIDI API to use to find ports",
            choices=apis)]
        answer = inquirer.prompt(q)
        conf.update(answer)

    def prompt_ports(self, conf):
        print('Looking for ports...')
        ports_in = io.get_input_ports()
        ports_out = io.get_output_ports()

        if not ports_in:
            raise Exception("No MIDI receiving ports found.")
        if not ports_out:
            raise Exception("No MIDI sending ports found.")

        q = [
            inquirer.List(
                'port_in',
                default=conf.get('port_in'),
                message="Which MIDI port for receiving?",
                choices=ports_in),
            inquirer.List(
                'port_out',
                default=conf.get('port_out'),
                message="Which MIDI port for sending?",
                choices=ports_out),
        ]
        answer = inquirer.prompt(q)
        conf.update(answer)
