# Patch management tool for the Boss GT-100

bogt is a command line tool for managing patches on the BOSS GT-100 guitar
effects processor. It uses the same TSL file format for storing patches as the
BOSS TONE STUDIO application.

Other than commands for the basic sending and receiving of patches.

To install, create a python virtualenv and install by running `pip install ./`

To begin use, connect your GT-100 (or GT-001) via USB, run `bogt configure` and
follow the prompts. Run `bogt help` for other available commands.

This tool supports an extension mechanism to add extra commands. See the
[bogt-rando](https://github.com/steveb/bogt-rando) repository for an extension
which adds the `bogt rand` command which generates mutated patches from a base
patch.

This project is licensed under the GNU GPL v3.
