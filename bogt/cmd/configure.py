import logging

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
        self.prompt_api(conf)
        io.set_backend(conf)
        self.prompt_ports(conf)
        config.save_config(conf)

        self.find_device(conf)
        config.save_config(conf)

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
