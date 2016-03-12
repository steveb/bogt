
import sys

class BogtShell(object):

    def main(self, argv):
        pass

def main(args=None):
    try:
        if args is None:
            args = sys.argv[1:]

        BogtShell().main(args)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        if '--debug' in args or '-d' in args:
            raise
        else:
            sys.stderr.write('%s\n' % e)
        sys.exit(1)

if __name__ == "__main__":
    main()

