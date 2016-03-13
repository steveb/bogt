
'''Patch management tool for the Boss GT-100'''

from cliff import app
from cliff import commandmanager

import sys

import bogt


class BogtApp(app.App):

    def __init__(self):
        super(BogtApp, self).__init__(
            description=__doc__.strip(),
            version=bogt.__version__,
            command_manager=commandmanager.CommandManager('bogt.cli'),
            deferred_help=True)

    def initialize_app(self, argv):
        pass


def main(argv=sys.argv[1:]):
    myapp = BogtApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
