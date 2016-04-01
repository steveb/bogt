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
        self.prompt_ports(conf)
        self.find_device(conf)
        config.save_config(conf)

    def find_device(self, conf):
        print('Looking for device...')
        sess = io.Session(conf)
        info = sess.query_device_info()
        print(info)

    def prompt_api(self, conf):
        apis = io.get_available_apis()
        choices = [a[1] for a in apis]
        api_dict = dict((a[1], a[0]) for a in apis)
        q = [inquirer.List(
            'api',
            message="Which MIDI API to use to find ports",
            choices=choices)]
        answer = inquirer.prompt(q)
        conf['api'] = api_dict[answer['api']]

    def prompt_ports(self, conf):
        api = conf['api']
        print('Looking for ports...')
        ports_in = io.get_input_ports(api)
        ports_out = io.get_output_ports(api)

        if not ports_in:
            raise Exception("No MIDI receiving ports found.")
        if not ports_out:
            raise Exception("No MIDI sending ports found.")

        q = [
            inquirer.List(
                'port_in',
                message="Which MIDI port for receiving?",
                choices=ports_in),
            inquirer.List(
                'port_out',
                message="Which MIDI port for sending?",
                choices=ports_out),
        ]
        answer = inquirer.prompt(q)
        conf.update(answer)
